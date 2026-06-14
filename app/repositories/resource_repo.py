from bson import ObjectId

from app.repositories.base import BaseRepository


class ResourceRepository(BaseRepository):
    collection_name = "resources"

    async def increment_downloads(self, resource_id: str) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(resource_id)}, {"$inc": {"downloads": 1}}
        )

    async def increment_views(self, resource_id: str) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(resource_id)}, {"$inc": {"views": 1}}
        )

    async def add_rating(self, resource_id: str, user_id: str, rating: float, review: str = "") -> None:
        resource = await self.find_by_id(resource_id)
        if not resource:
            raise ValueError("Resource not found")
        ratings = [r for r in resource.get("ratings", []) if r.get("user_id") != user_id]
        ratings.append({"user_id": user_id, "rating": rating, "review": review})
        avg = sum(r["rating"] for r in ratings) / len(ratings) if ratings else 0
        await self.collection.update_one(
            {"_id": ObjectId(resource_id)}, {"$set": {"ratings": ratings, "avg_rating": round(avg, 2)}}
        )

    async def toggle_bookmark(self, resource_id: str, user_id: str) -> bool:
        resource = await self.find_by_id(resource_id)
        if not resource:
            raise ValueError("Resource not found")
        bookmarks = resource.get("bookmarks", [])
        if user_id in bookmarks:
            await self.collection.update_one(
                {"_id": ObjectId(resource_id)}, {"$pull": {"bookmarks": user_id}}
            )
            return False
        await self.collection.update_one(
            {"_id": ObjectId(resource_id)}, {"$addToSet": {"bookmarks": user_id}}
        )
        return True

    async def count_by_uploader(self, uploader_id: str) -> int:
        return await self.collection.count_documents({"uploader_id": uploader_id})

    async def search(self, query: str, limit: int = 20) -> list[dict]:
        regex = {"$regex": query, "$options": "i"}
        cursor = self.collection.find(
            {"$or": [{"title": regex}, {"description": regex}, {"tags": regex}, {"course": regex}]},
            limit=limit,
        )
        docs = await cursor.to_list(limit)
        return [self.serialize(d) for d in docs if d]
