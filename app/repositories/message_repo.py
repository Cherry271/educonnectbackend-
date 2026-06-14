from datetime import datetime

from bson import ObjectId

from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository):
    collection_name = "messages"

    async def get_conversation_messages(
        self, conversation_id: str, page: int = 1, page_size: int = 50
    ) -> tuple[list[dict], int]:
        return await self.paginate(
            {"conversation_id": conversation_id}, page, page_size, sort=[("created_at", 1)]
        )

    async def mark_read(self, conversation_id: str, user_id: str) -> None:
        await self.collection.update_many(
            {"conversation_id": conversation_id, "sender_id": {"$ne": user_id}, "read_by": {"$ne": user_id}},
            {"$addToSet": {"read_by": user_id}},
        )


class ConversationRepository(BaseRepository):
    collection_name = "conversations"

    async def get_user_conversations(self, user_id: str) -> list[dict]:
        cursor = self.collection.find({"participants": user_id}).sort("last_message_at", -1)
        docs = await cursor.to_list(100)
        return [self.serialize(d) for d in docs if d]

    async def find_direct(self, user1: str, user2: str) -> dict | None:
        doc = await self.collection.find_one(
            {"is_group": False, "participants": {"$all": [user1, user2], "$size": 2}}
        )
        return self.serialize(doc)

    async def update_last_message(self, conversation_id: str, message: str) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {"last_message": message, "last_message_at": datetime.utcnow()}},
        )

    async def add_participants(self, conversation_id: str, user_ids: list[str]) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$addToSet": {"participants": {"$each": user_ids}}},
        )

    async def remove_participants(self, conversation_id: str, user_ids: list[str]) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$pullAll": {"participants": user_ids}},
        )

    async def set_typing(self, conversation_id: str, user_id: str, typing: bool) -> None:
        if typing:
            await self.collection.update_one(
                {"_id": ObjectId(conversation_id)}, {"$addToSet": {"typing_users": user_id}}
            )
        else:
            await self.collection.update_one(
                {"_id": ObjectId(conversation_id)}, {"$pull": {"typing_users": user_id}}
            )
