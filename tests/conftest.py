from datetime import datetime
from unittest.mock import AsyncMock, patch
import pytest
from bson import ObjectId


class MockCursor:
    def __init__(self, data):
        self.data = data
        self._limit = None
        self._skip = 0
        self._sort = None

    def sort(self, *args, **kwargs):
        self._sort = args
        return self

    def skip(self, count):
        self._skip = count
        return self

    def limit(self, count):
        self._limit = count
        return self

    async def to_list(self, length=None):
        res = self.data
        res = res[self._skip:]
        if self._limit is not None:
            res = res[:self._limit]
        return res


class MockCollection:
    def __init__(self, name):
        self.name = name
        self.docs = []

    async def find_one(self, filter_q):
        for doc in self.docs:
            if self._matches(doc, filter_q):
                return doc
        return None

    async def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self.docs.append(doc)
        class InsertResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return InsertResult(doc["_id"])

    async def update_one(self, filter_q, update_q):
        doc = await self.find_one(filter_q)
        if doc:
            set_dict = update_q.get("$set", {})
            for k, v in set_dict.items():
                doc[k] = v
            if "$addToSet" in update_q:
                for k, v in update_q["$addToSet"].items():
                    doc.setdefault(k, [])
                    if v not in doc[k]:
                        doc[k].append(v)
            if "$push" in update_q:
                for k, v in update_q["$push"].items():
                    doc.setdefault(k, []).append(v)
            if "$pull" in update_q:
                for k, v in update_q["$pull"].items():
                    doc.setdefault(k, [])
                    if v in doc[k]:
                        doc[k].remove(v)
            class UpdateResult:
                modified_count = 1
            return UpdateResult()
        class UpdateResult:
            modified_count = 0
        return UpdateResult()

    async def delete_one(self, filter_q):
        doc = await self.find_one(filter_q)
        if doc:
            self.docs.remove(doc)
            class DeleteResult:
                deleted_count = 1
            return DeleteResult()
        class DeleteResult:
            deleted_count = 0
        return DeleteResult()

    async def delete_many(self, filter_q):
        if not filter_q:
            self.docs = []
        else:
            self.docs = [d for d in self.docs if not self._matches(d, filter_q)]
        class DeleteResult:
            deleted_count = 1
        return DeleteResult()

    async def count_documents(self, filter_q):
        if not filter_q:
            return len(self.docs)
        count = 0
        for doc in self.docs:
            if self._matches(doc, filter_q):
                count += 1
        return count

    def find(self, filter_q=None, limit=None):
        filter_q = filter_q or {}
        matched = []
        for doc in self.docs:
            if self._matches(doc, filter_q):
                matched.append(doc)
        return MockCursor(matched)

    def _matches(self, doc, filter_q):
        for k, v in filter_q.items():
            if k == "$or":
                any_match = False
                for sub in v:
                    if self._matches(doc, sub):
                        any_match = True
                        break
                if not any_match:
                    return False
            elif k == "$nin":
                pass
            elif isinstance(v, dict):
                for op, val in v.items():
                    if op == "$in":
                        doc_val = doc.get(k)
                        if isinstance(doc_val, list):
                            if not any(x in val for x in doc_val):
                                return False
                        elif doc_val not in val:
                            return False
                    elif op == "$nin":
                        if doc.get(k) in val:
                            return False
                    elif op == "$gte":
                        if doc.get(k, datetime.min) < val:
                            return False
                    elif op == "$lte":
                        if doc.get(k, datetime.max) > val:
                            return False
            else:
                # String comparison conversion for ID matching
                val_to_compare = doc.get(k)
                if isinstance(val_to_compare, ObjectId):
                    val_to_compare = str(val_to_compare)
                compare_val = v
                if isinstance(compare_val, ObjectId):
                    compare_val = str(compare_val)
                if val_to_compare != compare_val:
                    return False
        return True


class MockAsyncMotorDatabase:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]

    def __getattr__(self, name):
        return self[name]


mock_db = MockAsyncMotorDatabase()


@pytest.fixture(autouse=True)
def mock_mongodb():
    import app.database.mongodb
    app.database.mongodb._db = mock_db
    with patch("app.database.mongodb.get_database", return_value=mock_db), \
         patch("app.repositories.base.get_database", return_value=mock_db), \
         patch("app.core.dependencies.get_database", return_value=mock_db), \
         patch("app.database.mongodb.connect_to_mongo", AsyncMock()), \
         patch("app.database.mongodb.close_mongo_connection", AsyncMock()):
        yield
