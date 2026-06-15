from typing import Optional
from app.repositories.base import BaseRepository


class SchoolRepository(BaseRepository):
    collection_name = "schools"

    async def find_by_name(self, name: str) -> Optional[dict]:
        doc = await self.collection.find_one({"name": name})
        return self.serialize(doc)

    async def search_schools(self, query: str, limit: int = 20) -> list[dict]:
        regex = {"$regex": query, "$options": "i"}
        cursor = self.collection.find(
            {"$or": [{"name": regex}, {"domain": regex}]},
            limit=limit,
        )
        docs = await cursor.to_list(limit)
        return [self.serialize(d) for d in docs if d]
