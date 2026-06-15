from datetime import datetime
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository):
    collection_name = "events"

    async def get_upcoming_events(self, reference_ids: list[str] | None = None, limit: int = 10) -> list[dict]:
        now = datetime.utcnow()
        filter_q = {"end_time": {"$gte": now}}
        if reference_ids is not None:
            filter_q["$or"] = [
                {"reference_id": {"$in": reference_ids}},
                {"reference_id": None}
            ]
        cursor = self.collection.find(filter_q).sort("start_time", 1).limit(limit)
        docs = await cursor.to_list(limit)
        return [self.serialize(d) for d in docs if d]
