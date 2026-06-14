from datetime import datetime
from typing import Optional

from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    collection_name = "users"

    async def find_by_email(self, email: str) -> Optional[dict]:
        doc = await self.collection.find_one({"email": email.lower()})
        return self.serialize(doc)

    async def find_by_username(self, username: str) -> Optional[dict]:
        doc = await self.collection.find_one({"username": username.lower()})
        return self.serialize(doc)

    async def find_by_identifier(self, identifier: str) -> Optional[dict]:
        identifier = identifier.lower()
        doc = await self.collection.find_one(
            {"$or": [{"email": identifier}, {"username": identifier}]}
        )
        return self.serialize(doc)

    async def search_users(self, query: str, limit: int = 20) -> list[dict]:
        regex = {"$regex": query, "$options": "i"}
        cursor = self.collection.find(
            {"$or": [{"username": regex}, {"first_name": regex}, {"last_name": regex}, {"email": regex}]},
            limit=limit,
        )
        docs = await cursor.to_list(limit)
        return [self.serialize(d) for d in docs if d]

    async def follow(self, user_id: str, target_id: str) -> None:
        oid = self.to_object_id(user_id)
        target_oid = self.to_object_id(target_id)
        await self.collection.update_one({"_id": oid}, {"$addToSet": {"following": target_id}})
        await self.collection.update_one({"_id": target_oid}, {"$addToSet": {"followers": user_id}})

    async def unfollow(self, user_id: str, target_id: str) -> None:
        oid = self.to_object_id(user_id)
        target_oid = self.to_object_id(target_id)
        await self.collection.update_one({"_id": oid}, {"$pull": {"following": target_id}})
        await self.collection.update_one({"_id": target_oid}, {"$pull": {"followers": user_id}})

    async def update_profile(self, user_id: str, data: dict) -> Optional[dict]:
        data["updated_at"] = datetime.utcnow()
        return await self.update(user_id, data)
