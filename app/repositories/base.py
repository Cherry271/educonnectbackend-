from typing import Any, Generic, List, Optional, TypeVar

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from app.database.mongodb import get_database

T = TypeVar("T")


class BaseRepository(Generic[T]):
    collection_name: str

    def __init__(self) -> None:
        self._db: Optional[AsyncIOMotorDatabase] = None

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._db is None:
            self._db = get_database()
        return self._db

    @property
    def collection(self) -> AsyncIOMotorCollection:
        return self.db[self.collection_name]

    @staticmethod
    def to_object_id(id_str: str) -> ObjectId:
        return ObjectId(id_str)

    @staticmethod
    def serialize(doc: Optional[dict]) -> Optional[dict]:
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id"))
        return doc

    async def find_by_id(self, id_str: str) -> Optional[dict]:
        doc = await self.collection.find_one({"_id": self.to_object_id(id_str)})
        return self.serialize(doc)

    async def create(self, data: dict) -> dict:
        result = await self.collection.insert_one(data)
        return await self.find_by_id(str(result.inserted_id))  # type: ignore

    async def update(self, id_str: str, data: dict) -> Optional[dict]:
        await self.collection.update_one({"_id": self.to_object_id(id_str)}, {"$set": data})
        return await self.find_by_id(id_str)

    async def delete(self, id_str: str) -> bool:
        result = await self.collection.delete_one({"_id": self.to_object_id(id_str)})
        return result.deleted_count > 0

    async def paginate(
        self, filter_query: dict, page: int = 1, page_size: int = 20, sort: Optional[List[tuple]] = None
    ) -> tuple[List[dict], int]:
        skip = (page - 1) * page_size
        cursor = self.collection.find(filter_query)
        if sort:
            cursor = cursor.sort(sort)
        total = await self.collection.count_documents(filter_query)
        docs = await cursor.skip(skip).limit(page_size).to_list(page_size)
        return [self.serialize(d) for d in docs if d], total
