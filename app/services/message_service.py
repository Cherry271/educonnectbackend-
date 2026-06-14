from datetime import datetime

from app.repositories.message_repo import ConversationRepository, MessageRepository
from app.repositories.user_repo import UserRepository
from app.schemas.message import ConversationCreate, ConversationResponse, MessageCreate, MessageResponse
from app.services.notification_service import NotificationService


class MessageService:
    def __init__(self) -> None:
        self.message_repo = MessageRepository()
        self.conversation_repo = ConversationRepository()
        self.user_repo = UserRepository()
        self.notification_service = NotificationService()
        self._socket_manager = None

    def set_socket_manager(self, manager) -> None:
        self._socket_manager = manager

    async def _enrich_message(self, msg: dict) -> MessageResponse:
        sender = await self.user_repo.find_by_id(msg["sender_id"])
        return MessageResponse(
            id=msg["id"],
            conversation_id=msg["conversation_id"],
            sender_id=msg["sender_id"],
            sender_name=f"{sender['first_name']} {sender['last_name']}" if sender else "",
            content=msg.get("content", ""),
            file_url=msg.get("file_url", ""),
            voice_url=msg.get("voice_url", ""),
            message_type=msg.get("message_type", "text"),
            read_by=msg.get("read_by", []),
            created_at=msg.get("created_at", datetime.utcnow()),
        )

    async def create_conversation(self, user_id: str, data: ConversationCreate) -> ConversationResponse:
        participants = list(set([user_id] + data.participant_ids))
        if not data.is_group and len(participants) == 2:
            existing = await self.conversation_repo.find_direct(participants[0], participants[1])
            if existing:
                return await self._enrich_conversation(existing, user_id)

        doc = {
            "participants": participants,
            "is_group": data.is_group,
            "group_name": data.group_name,
            "last_message": "",
            "last_message_at": datetime.utcnow(),
            "typing_users": [],
            "created_at": datetime.utcnow(),
        }
        conv = await self.conversation_repo.create(doc)
        return await self._enrich_conversation(conv, user_id)

    async def _enrich_conversation(self, conv: dict, user_id: str) -> ConversationResponse:
        names = []
        for pid in conv.get("participants", []):
            if pid != user_id:
                u = await self.user_repo.find_by_id(pid)
                if u:
                    names.append(f"{u['first_name']} {u['last_name']}")
        unread = await self.message_repo.collection.count_documents(
            {"conversation_id": conv["id"], "sender_id": {"$ne": user_id}, "read_by": {"$ne": user_id}}
        )
        return ConversationResponse(
            id=conv["id"],
            participants=conv.get("participants", []),
            participant_names=names,
            is_group=conv.get("is_group", False),
            group_name=conv.get("group_name", ""),
            last_message=conv.get("last_message", ""),
            last_message_at=conv.get("last_message_at", datetime.utcnow()),
            unread_count=unread,
        )

    async def get_conversations(self, user_id: str) -> list[ConversationResponse]:
        convs = await self.conversation_repo.get_user_conversations(user_id)
        return [await self._enrich_conversation(c, user_id) for c in convs]

    async def send_message(self, conversation_id: str, sender_id: str, data: MessageCreate) -> MessageResponse:
        doc = {
            **data.model_dump(),
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "read_by": [sender_id],
            "created_at": datetime.utcnow(),
        }
        msg = await self.message_repo.create(doc)
        await self.conversation_repo.update_last_message(conversation_id, data.content or "Attachment")
        enriched = await self._enrich_message(msg)

        conv = await self.conversation_repo.find_by_id(conversation_id)
        if conv:
            for pid in conv.get("participants", []):
                if pid != sender_id:
                    await self.notification_service.notify_message(pid, sender_id, conversation_id)
                    if self._socket_manager:
                        await self._socket_manager.send_to_user(pid, "new_message", enriched.model_dump())

        return enriched

    async def get_messages(self, conversation_id: str, user_id: str, page: int = 1) -> tuple[list[MessageResponse], int]:
        await self.message_repo.mark_read(conversation_id, user_id)
        msgs, total = await self.message_repo.get_conversation_messages(conversation_id, page)
        return [await self._enrich_message(m) for m in msgs], total
