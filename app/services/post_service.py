from datetime import datetime

from app.repositories.post_repo import PostRepository
from app.repositories.user_repo import UserRepository
from app.schemas.post import CommentCreate, PostCreate, PostResponse, PostUpdate
from app.services.notification_service import NotificationService


class PostService:
    def __init__(self) -> None:
        self.post_repo = PostRepository()
        self.user_repo = UserRepository()
        self.notification_service = NotificationService()

    async def _enrich(
        self, post: dict, current_user_id: str | None = None
    ) -> PostResponse:
        author = await self.user_repo.find_by_id(post["author_id"])
        author_name = (
            f"{author['first_name']} {author['last_name']}" if author else "Unknown"
        )
        likes = post.get("likes", [])
        bookmarks = post.get("bookmarks", [])
        return PostResponse(
            id=post["id"],
            author_id=post["author_id"],
            author_name=author_name,
            author_avatar=author.get("profile_picture", "") if author else "",
            author_role=author.get("role", "") if author else "",
            author_department=author.get("department", "") if author else "",
            content=post.get("content", ""),
            post_type=post.get("post_type", "text"),
            media_url=post.get("media_url", ""),
            resource_id=post.get("resource_id"),
            poll_question=post.get("poll_question", ""),
            poll_options=post.get("poll_options", []),
            tags=post.get("tags", []),
            department=post.get("department", ""),
            likes_count=len(likes),
            comments_count=len(post.get("comments", [])),
            shares_count=len(post.get("shares", [])),
            is_liked=current_user_id in likes if current_user_id else False,
            is_bookmarked=current_user_id in bookmarks if current_user_id else False,
            is_edited=post.get("is_edited", False),
            created_at=post.get("created_at", datetime.utcnow()),
            updated_at=post.get("updated_at", datetime.utcnow()),
        )

    async def create(self, author_id: str, data: PostCreate) -> PostResponse:
        if data.content:
            try:
                from app.ai.moderation_service import moderation_service

                mod = await moderation_service.moderate(data.content)
                if not mod.is_safe:
                    raise ValueError(f"Content flagged: {mod.reason}")
            except Exception:
                # AI moderation not available — skip moderation in dev/core mode
                pass

        author = await self.user_repo.find_by_id(author_id)
        doc = {
            **data.model_dump(),
            "post_type": data.post_type.value,
            "author_id": author_id,
            "department": data.department
            or (author.get("department", "") if author else ""),
            "likes": [],
            "comments": [],
            "shares": [],
            "bookmarks": [],
            "reports": [],
            "is_edited": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        post = await self.post_repo.create(doc)
        return await self._enrich(post, author_id)

    async def get_feed(
        self,
        page: int,
        page_size: int,
        user_id: str | None = None,
        department: str | None = None,
    ):
        posts, total = await self.post_repo.get_feed(page, page_size, department)
        items = [await self._enrich(p, user_id) for p in posts]
        return items, total

    async def update(
        self, post_id: str, author_id: str, data: PostUpdate
    ) -> PostResponse:
        post = await self.post_repo.find_by_id(post_id)
        if not post or post["author_id"] != author_id:
            raise ValueError("Post not found or unauthorized")
        update = data.model_dump(exclude_none=True)
        update["is_edited"] = True
        update["updated_at"] = datetime.utcnow()
        updated = await self.post_repo.update(post_id, update)
        return await self._enrich(updated, author_id)  # type: ignore

    async def delete(self, post_id: str, author_id: str) -> None:
        post = await self.post_repo.find_by_id(post_id)
        if not post or post["author_id"] != author_id:
            raise ValueError("Post not found or unauthorized")
        await self.post_repo.delete(post_id)

    async def like(self, post_id: str, user_id: str) -> dict:
        result = await self.post_repo.toggle_like(post_id, user_id)
        if result["liked"]:
            post = await self.post_repo.find_by_id(post_id)
            if post and post["author_id"] != user_id:
                await self.notification_service.notify_like(
                    post["author_id"], user_id, post_id
                )
        return result

    async def comment(
        self, post_id: str, user_id: str, data: CommentCreate
    ) -> PostResponse:
        comment = {
            "author_id": user_id,
            "content": data.content,
            "likes": [],
            "replies": [],
        }
        post = await self.post_repo.add_comment(post_id, comment)
        post_obj = await self.post_repo.find_by_id(post_id)
        if post_obj and post_obj["author_id"] != user_id:
            await self.notification_service.notify_comment(
                post_obj["author_id"], user_id, post_id
            )
        return await self._enrich(post, user_id)  # type: ignore

    async def bookmark(self, post_id: str, user_id: str) -> bool:
        return await self.post_repo.toggle_bookmark(post_id, user_id)

    async def share(self, post_id: str, user_id: str) -> None:
        from bson import ObjectId

        await self.post_repo.collection.update_one(
            {"_id": ObjectId(post_id)}, {"$addToSet": {"shares": user_id}}
        )

    async def report(self, post_id: str, user_id: str, reason: str) -> None:
        from bson import ObjectId

        await self.post_repo.collection.update_one(
            {"_id": ObjectId(post_id)},
            {
                "$push": {
                    "reports": {
                        "user_id": user_id,
                        "reason": reason,
                        "created_at": datetime.utcnow(),
                    }
                }
            },
        )
