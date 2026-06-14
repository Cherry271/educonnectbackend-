from datetime import datetime
from typing import Optional

from bson import ObjectId

from app.repositories.base import BaseRepository


class PostRepository(BaseRepository):
    collection_name = "posts"

    async def get_feed(self, page: int = 1, page_size: int = 20, department: Optional[str] = None) -> tuple[list[dict], int]:
        query: dict = {}
        if department:
            query["department"] = department
        return await self.paginate(query, page, page_size, sort=[("created_at", -1)])

    async def toggle_like(self, post_id: str, user_id: str) -> dict:
        post = await self.find_by_id(post_id)
        if not post:
            raise ValueError("Post not found")
        likes = post.get("likes", [])
        if user_id in likes:
            await self.collection.update_one(
                {"_id": ObjectId(post_id)}, {"$pull": {"likes": user_id}}
            )
            liked = False
        else:
            await self.collection.update_one(
                {"_id": ObjectId(post_id)}, {"$addToSet": {"likes": user_id}}
            )
            liked = True
        updated = await self.find_by_id(post_id)
        return {"liked": liked, "likes_count": len(updated.get("likes", [])) if updated else 0}

    async def toggle_bookmark(self, post_id: str, user_id: str) -> bool:
        post = await self.find_by_id(post_id)
        if not post:
            raise ValueError("Post not found")
        bookmarks = post.get("bookmarks", [])
        if user_id in bookmarks:
            await self.collection.update_one(
                {"_id": ObjectId(post_id)}, {"$pull": {"bookmarks": user_id}}
            )
            return False
        await self.collection.update_one(
            {"_id": ObjectId(post_id)}, {"$addToSet": {"bookmarks": user_id}}
        )
        return True

    async def add_comment(self, post_id: str, comment: dict) -> Optional[dict]:
        comment["id"] = str(ObjectId())
        comment["created_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(post_id)}, {"$push": {"comments": comment}}
        )
        return await self.find_by_id(post_id)

    async def count_by_author(self, author_id: str) -> int:
        return await self.collection.count_documents({"author_id": author_id})
