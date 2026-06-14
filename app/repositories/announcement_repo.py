from datetime import datetime

from app.repositories.base import BaseRepository


class AnnouncementRepository(BaseRepository):
    collection_name = "announcements"

    async def get_active(self, page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
        now = datetime.utcnow()
        query = {
            "is_active": True,
            "$or": [{"expires_at": None}, {"expires_at": {"$gt": now}}],
        }
        return await self.paginate(query, page, page_size, sort=[("priority", -1), ("created_at", -1)])
