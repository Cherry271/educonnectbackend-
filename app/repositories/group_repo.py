from bson import ObjectId

from app.repositories.base import BaseRepository


class GroupRepository(BaseRepository):
    collection_name = "groups"

    async def join(self, group_id: str, user_id: str) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(group_id)},
            {"$addToSet": {"members": user_id}, "$pull": {"invited": user_id}},
        )

    async def leave(self, group_id: str, user_id: str) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(group_id)}, {"$pull": {"members": user_id, "moderators": user_id}}
        )

    async def invite(self, group_id: str, user_ids: list[str]) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(group_id)}, {"$addToSet": {"invited": {"$each": user_ids}}}
        )

    async def search(self, query: str, limit: int = 20) -> list[dict]:
        regex = {"$regex": query, "$options": "i"}
        cursor = self.collection.find(
            {"$or": [{"name": regex}, {"description": regex}, {"department": regex}]},
            limit=limit,
        )
        docs = await cursor.to_list(limit)
        return [self.serialize(d) for d in docs if d]
