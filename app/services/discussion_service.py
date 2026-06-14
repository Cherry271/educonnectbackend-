from datetime import datetime

from app.repositories.discussion_repo import DiscussionRepository
from app.repositories.user_repo import UserRepository
from app.schemas.discussion import DiscussionCreate, DiscussionResponse


class DiscussionService:
    def __init__(self) -> None:
        self.repo = DiscussionRepository()
        self.user_repo = UserRepository()

    async def _enrich(self, discussion: dict, user_id: str | None = None) -> DiscussionResponse:
        author = await self.user_repo.find_by_id(discussion["author_id"])
        likes = discussion.get("likes", [])
        return DiscussionResponse(
            id=discussion["id"],
            author_id=discussion["author_id"],
            author_name=f"{author['first_name']} {author['last_name']}" if author else "",
            title=discussion["title"],
            content=discussion["content"],
            tags=discussion.get("tags", []),
            department=discussion.get("department", ""),
            likes_count=len(likes),
            comments_count=len(discussion.get("comments", [])),
            is_liked=user_id in likes if user_id else False,
            is_pinned=discussion.get("is_pinned", False),
            trending_score=discussion.get("trending_score", 0),
            views=discussion.get("views", 0),
            created_at=discussion.get("created_at", datetime.utcnow()),
        )

    async def create(self, author_id: str, data: DiscussionCreate) -> DiscussionResponse:
        author = await self.user_repo.find_by_id(author_id)
        doc = {
            **data.model_dump(),
            "author_id": author_id,
            "department": data.department or (author.get("department", "") if author else ""),
            "likes": [],
            "comments": [],
            "is_pinned": False,
            "trending_score": 1.0,
            "views": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        discussion = await self.repo.create(doc)
        return await self._enrich(discussion, author_id)

    async def list_discussions(self, page: int, page_size: int, user_id: str | None = None):
        items, total = await self.repo.paginate({}, page, page_size, sort=[("is_pinned", -1), ("created_at", -1)])
        return [await self._enrich(i, user_id) for i in items], total

    async def get_trending(self, user_id: str | None = None) -> list[DiscussionResponse]:
        items = await self.repo.get_trending()
        return [await self._enrich(i, user_id) for i in items]

    async def get(self, discussion_id: str, user_id: str | None = None) -> DiscussionResponse:
        await self.repo.increment_views(discussion_id)
        discussion = await self.repo.find_by_id(discussion_id)
        if not discussion:
            raise ValueError("Discussion not found")
        return await self._enrich(discussion, user_id)

    async def pin(self, discussion_id: str, pinned: bool = True) -> None:
        await self.repo.pin(discussion_id, pinned)

    async def delete(self, discussion_id: str, user_id: str, user_role: str | None = None) -> None:
        discussion = await self.repo.find_by_id(discussion_id)
        if not discussion:
            raise ValueError("Discussion not found")
        if discussion["author_id"] != user_id and user_role not in ["teacher", "admin"]:
            raise ValueError("Not authorized to delete discussion")
        await self.repo.delete(discussion_id)

    async def like(self, discussion_id: str, user_id: str) -> dict:
        return await self.repo.toggle_like(discussion_id, user_id)

    async def add_comment(self, discussion_id: str, user_id: str, content: str) -> None:
        await self.repo.add_comment(discussion_id, {"author_id": user_id, "content": content, "likes": [], "replies": []})
