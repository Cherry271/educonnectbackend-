from datetime import datetime

from app.repositories.announcement_repo import AnnouncementRepository
from app.repositories.user_repo import UserRepository
from app.schemas.announcement import AnnouncementCreate, AnnouncementResponse
from app.services.notification_service import NotificationService


class AnnouncementService:
    def __init__(self) -> None:
        self.repo = AnnouncementRepository()
        self.user_repo = UserRepository()
        self.notification_service = NotificationService()

    async def _enrich(self, announcement: dict) -> AnnouncementResponse:
        author = await self.user_repo.find_by_id(announcement["author_id"])
        return AnnouncementResponse(
            id=announcement["id"],
            author_id=announcement["author_id"],
            author_name=f"{author['first_name']} {author['last_name']}" if author else "",
            title=announcement["title"],
            content=announcement["content"],
            announcement_type=announcement.get("announcement_type", "announcement"),
            priority=announcement.get("priority", "medium"),
            department=announcement.get("department", ""),
            scheduled_at=announcement.get("scheduled_at"),
            expires_at=announcement.get("expires_at"),
            is_active=announcement.get("is_active", True),
            created_at=announcement.get("created_at", datetime.utcnow()),
        )

    async def create(self, author_id: str, data: AnnouncementCreate) -> AnnouncementResponse:
        doc = {
            **data.model_dump(),
            "announcement_type": data.announcement_type.value,
            "priority": data.priority.value,
            "author_id": author_id,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        announcement = await self.repo.create(doc)

        # Notify users in department
        if data.department:
            cursor = self.user_repo.collection.find({"department": data.department}).limit(100)
            users = await cursor.to_list(100)
            for u in users:
                await self.notification_service.notify_announcement(str(u["_id"]), announcement["id"], data.title)

        return await self._enrich(announcement)

    async def list_active(self, page: int, page_size: int):
        items, total = await self.repo.get_active(page, page_size)
        return [await self._enrich(i) for i in items], total
