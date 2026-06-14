from datetime import datetime

from bson import ObjectId

from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    collection_name = "notifications"

    async def get_user_notifications(self, user_id: str, page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
        return await self.paginate({"user_id": user_id}, page, page_size, sort=[("created_at", -1)])

    async def mark_read(self, notification_id: str, user_id: str) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(notification_id), "user_id": user_id},
            {"$set": {"is_read": True}},
        )

    async def mark_all_read(self, user_id: str) -> None:
        await self.collection.update_one(
            {"user_id": user_id, "is_read": False},
            {"$set": {"is_read": True}},
            upsert=False,
        )
        await self.collection.update_many({"user_id": user_id, "is_read": False}, {"$set": {"is_read": True}})

    async def unread_count(self, user_id: str) -> int:
        return await self.collection.count_documents({"user_id": user_id, "is_read": False})
