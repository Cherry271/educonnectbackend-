from datetime import datetime

from bson import ObjectId

from app.repositories.base import BaseRepository


class DiscussionRepository(BaseRepository):
    collection_name = "discussions"

    async def get_trending(self, limit: int = 10) -> list[dict]:
        cursor = self.collection.find().sort("trending_score", -1).limit(limit)
        docs = await cursor.to_list(limit)
        return [self.serialize(d) for d in docs if d]

    async def increment_views(self, discussion_id: str) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(discussion_id)}, {"$inc": {"views": 1}}
        )

    async def toggle_like(self, discussion_id: str, user_id: str) -> dict:
        discussion = await self.find_by_id(discussion_id)
        if not discussion:
            raise ValueError("Discussion not found")
        likes = discussion.get("likes", [])
        if user_id in likes:
            await self.collection.update_one(
                {"_id": ObjectId(discussion_id)}, {"$pull": {"likes": user_id}, "$inc": {"trending_score": -1}}
            )
            liked = False
        else:
            await self.collection.update_one(
                {"_id": ObjectId(discussion_id)}, {"$addToSet": {"likes": user_id}, "$inc": {"trending_score": 2}}
            )
            liked = True
        updated = await self.find_by_id(discussion_id)
        return {"liked": liked, "likes_count": len(updated.get("likes", [])) if updated else 0}

    async def add_comment(self, discussion_id: str, comment: dict) -> None:
        comment["id"] = str(ObjectId())
        comment["created_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(discussion_id)},
            {"$push": {"comments": comment}, "$inc": {"trending_score": 3}},
        )

    async def pin(self, discussion_id: str, pinned: bool = True) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(discussion_id)}, {"$set": {"is_pinned": pinned}}
        )
