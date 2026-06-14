from datetime import datetime

from app.repositories.group_repo import GroupRepository
from app.repositories.message_repo import ConversationRepository
from app.schemas.group import GroupCreate, GroupResponse


class GroupService:
    def __init__(self) -> None:
        self.repo = GroupRepository()
        self.conversation_repo = ConversationRepository()

    async def _enrich(self, group: dict, user_id: str | None = None) -> GroupResponse:
        return GroupResponse(
            id=group["id"],
            name=group["name"],
            description=group.get("description", ""),
            group_type=group.get("group_type", "study"),
            department=group.get("department", ""),
            course=group.get("course", ""),
            creator_id=group["creator_id"],
            members_count=len(group.get("members", [])),
            is_member=user_id in group.get("members", []) if user_id else False,
            is_private=group.get("is_private", False),
            cover_image=group.get("cover_image", ""),
            conversation_id=group.get("conversation_id"),
            created_at=group.get("created_at", datetime.utcnow()),
        )

    async def _create_group_conversation(
        self, group_name: str, participants: list[str]
    ) -> str:
        doc = {
            "participants": participants,
            "is_group": True,
            "group_name": group_name,
            "last_message": "",
            "last_message_at": datetime.utcnow(),
            "typing_users": [],
            "created_at": datetime.utcnow(),
        }
        conv = await self.conversation_repo.create(doc)
        return conv["id"]

    async def create(self, creator_id: str, data: GroupCreate) -> GroupResponse:
        doc = {
            **data.model_dump(),
            "group_type": data.group_type.value,
            "creator_id": creator_id,
            "members": [creator_id],
            "moderators": [creator_id],
            "invited": [],
            "resource_ids": [],
            "created_at": datetime.utcnow(),
        }
        group = await self.repo.create(doc)
        conversation_id = await self._create_group_conversation(
            group["name"], [creator_id]
        )
        await self.repo.update(group["id"], {"conversation_id": conversation_id})
        group["conversation_id"] = conversation_id
        return await self._enrich(group, creator_id)

    async def list_groups(self, page: int, page_size: int, user_id: str | None = None):
        items, total = await self.repo.paginate(
            {}, page, page_size, sort=[("created_at", -1)]
        )
        return [await self._enrich(i, user_id) for i in items], total

    async def join(self, group_id: str, user_id: str) -> None:
        await self.repo.join(group_id, user_id)
        group = await self.repo.find_by_id(group_id)
        if not group:
            raise ValueError("Group not found")

        conversation_id = group.get("conversation_id")
        if conversation_id:
            await self.conversation_repo.add_participants(conversation_id, [user_id])
        else:
            conversation_id = await self._create_group_conversation(
                group["name"], group.get("members", [])
            )
            await self.repo.update(group_id, {"conversation_id": conversation_id})

    async def leave(self, group_id: str, user_id: str) -> None:
        await self.repo.leave(group_id, user_id)
        group = await self.repo.find_by_id(group_id)
        if group and group.get("conversation_id"):
            await self.conversation_repo.remove_participants(
                group["conversation_id"], [user_id]
            )

    async def invite(self, group_id: str, user_ids: list[str]) -> None:
        await self.repo.invite(group_id, user_ids)
