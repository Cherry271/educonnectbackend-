from datetime import datetime

from app.models.enums import NotificationType
from app.repositories.notification_repo import NotificationRepository


class NotificationService:
    def __init__(self) -> None:
        self.repo = NotificationRepository()
        self._socket_manager = None

    def set_socket_manager(self, manager) -> None:
        self._socket_manager = manager

    async def create(
        self, user_id: str, notification_type: NotificationType, title: str, message: str, data: dict | None = None
    ) -> dict:
        doc = {
            "user_id": user_id,
            "notification_type": notification_type.value,
            "title": title,
            "message": message,
            "data": data or {},
            "is_read": False,
            "created_at": datetime.utcnow(),
        }
        notification = await self.repo.create(doc)
        if self._socket_manager:
            await self._socket_manager.send_to_user(user_id, "notification", notification)
        return notification

    async def notify_like(self, user_id: str, actor_id: str, post_id: str) -> None:
        await self.create(user_id, NotificationType.LIKE, "New Like", "Someone liked your post", {"post_id": post_id, "actor_id": actor_id})

    async def notify_comment(self, user_id: str, actor_id: str, post_id: str) -> None:
        await self.create(user_id, NotificationType.COMMENT, "New Comment", "Someone commented on your post", {"post_id": post_id, "actor_id": actor_id})

    async def notify_follow(self, user_id: str, actor_id: str) -> None:
        await self.create(user_id, NotificationType.FOLLOW, "New Follower", "Someone started following you", {"actor_id": actor_id})

    async def notify_resource(self, user_id: str, actor_id: str, resource_id: str) -> None:
        await self.create(user_id, NotificationType.RESOURCE, "New Resource", "New resource uploaded", {"resource_id": resource_id, "actor_id": actor_id})

    async def notify_announcement(self, user_id: str, announcement_id: str, title: str) -> None:
        await self.create(user_id, NotificationType.ANNOUNCEMENT, "Announcement", title, {"announcement_id": announcement_id})

    async def notify_message(self, user_id: str, sender_id: str, conversation_id: str) -> None:
        await self.create(user_id, NotificationType.MESSAGE, "New Message", "You have a new message", {"conversation_id": conversation_id, "sender_id": sender_id})
