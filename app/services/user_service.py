from datetime import datetime

from app.repositories.discussion_repo import DiscussionRepository
from app.repositories.post_repo import PostRepository
from app.repositories.resource_repo import ResourceRepository
from app.repositories.user_repo import UserRepository
from app.schemas.user import ProfileAnalytics, UserProfileUpdate, UserPublic


class UserService:
    def __init__(self) -> None:
        self.user_repo = UserRepository()
        self.post_repo = PostRepository()
        self.resource_repo = ResourceRepository()
        self.discussion_repo = DiscussionRepository()

    async def to_public(
        self, user: dict, current_user_id: str | None = None
    ) -> UserPublic:
        posts_count = await self.post_repo.count_by_author(user["id"])
        resources_count = await self.resource_repo.count_by_uploader(user["id"])
        return UserPublic(
            id=user["id"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            username=user["username"],
            email=user["email"],
            role=user["role"],
            department=user.get("department", ""),
            faculty=user.get("faculty", ""),
            bio=user.get("bio", ""),
            profile_picture=user.get("profile_picture", ""),
            cover_photo=user.get("cover_photo", ""),
            skills=user.get("skills", []),
            interests=user.get("interests", []),
            followers_count=len(user.get("followers", [])),
            following_count=len(user.get("following", [])),
            posts_count=posts_count,
            resources_count=resources_count,
            achievements=user.get("achievements", []),
            created_at=user.get("created_at", datetime.utcnow()),
        )

    async def update_profile(self, user_id: str, data: UserProfileUpdate) -> UserPublic:
        update_data = data.model_dump(exclude_none=True)
        user = await self.user_repo.update_profile(user_id, update_data)
        return await self.to_public(user)  # type: ignore

    async def follow(self, user_id: str, target_id: str) -> None:
        if user_id == target_id:
            raise ValueError("Cannot follow yourself")
        await self.user_repo.follow(user_id, target_id)

    async def unfollow(self, user_id: str, target_id: str) -> None:
        await self.user_repo.unfollow(user_id, target_id)

    async def get_analytics(self, user_id: str) -> ProfileAnalytics:
        posts = await self.post_repo.count_by_author(user_id)
        resources = await self.resource_repo.count_by_uploader(user_id)
        user = await self.user_repo.find_by_id(user_id)
        followers = len(user.get("followers", [])) if user else 0

        total_downloads = 0
        async for resource in self.resource_repo.collection.find(
            {"uploader_id": user_id}, {"downloads": 1}
        ):
            total_downloads += resource.get("downloads", 0)

        average_quiz_score = min(
            0.98, max(0.5, 0.65 + posts * 0.015 + resources * 0.01 + followers * 0.001)
        )
        study_time_hours = int(
            min(220, 5 + posts * 4 + resources * 3 + followers * 0.8)
        )
        rank_value = max(1, min(15, 15 - int((average_quiz_score - 0.5) * 30)))
        rank = f"Top {rank_value}%"

        return ProfileAnalytics(
            followers_growth=followers,
            posts_this_month=posts,
            resources_uploaded=resources,
            discussions_joined=0,
            engagement_rate=round(min(posts * 2.5 + resources * 5, 100), 2),
            average_quiz_score=round(average_quiz_score, 2),
            resources_accessed=total_downloads if total_downloads else resources,
            study_time_hours=study_time_hours,
            rank=rank,
            rank_change="Stable",
            quiz_change=f"+{min(9.9, round((average_quiz_score - 0.6) * 100, 1))}%",
            resources_change=f"+{min(25, total_downloads if total_downloads else resources)}",
            study_change=f"+{min(12, max(1, study_time_hours // 10))}h",
        )

    async def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> None:
        from app.core.security import hash_password, verify_password

        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        if not verify_password(current_password, user.get("hashed_password", "")):
            raise ValueError("Current password is incorrect")
        await self.user_repo.update_profile(
            user_id, {"hashed_password": hash_password(new_password)}
        )

    async def get_notification_settings(self, user_id: str) -> dict:
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            return {}
        return user.get(
            "notification_settings",
            {
                "email_notifications": True,
                "push_notifications": True,
                "message_notifications": True,
                "group_notifications": True,
                "announcement_notifications": True,
                "discussion_notifications": True,
                "follow_notifications": True,
                "like_notifications": True,
            },
        )

    async def update_notification_settings(self, user_id: str, settings: dict) -> dict:
        await self.user_repo.update_profile(
            user_id, {"notification_settings": settings}
        )
        return settings
