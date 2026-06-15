from datetime import datetime
from typing import List, Optional, Tuple
from app.repositories.event_repo import EventRepository
from app.schemas.event import EventCreate, EventUpdate, EventResponse


class EventService:
    def __init__(self) -> None:
        self.event_repo = EventRepository()

    async def _enrich(self, event: dict) -> EventResponse:
        return EventResponse(
            id=event["id"],
            title=event["title"],
            description=event.get("description", ""),
            start_time=event["start_time"],
            end_time=event["end_time"],
            event_type=event.get("event_type", "event"),
            reference_id=event.get("reference_id"),
            created_by=event["created_by"],
            created_at=event.get("created_at", datetime.utcnow()),
        )

    async def create(self, creator_id: str, data: EventCreate) -> EventResponse:
        doc = {
            **data.model_dump(),
            "created_by": creator_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        res = await self.event_repo.create(doc)
        return await self._enrich(res)

    async def get(self, event_id: str) -> EventResponse:
        res = await self.event_repo.find_by_id(event_id)
        if not res:
            raise ValueError("Event not found")
        return await self._enrich(res)

    async def list_events(
        self, reference_id: Optional[str] = None, page: int = 1, page_size: int = 20
    ) -> Tuple[List[EventResponse], int]:
        filter_q = {}
        if reference_id:
            filter_q["reference_id"] = reference_id
        items, total = await self.event_repo.paginate(filter_q, page, page_size, sort=[("start_time", 1)])
        return [await self._enrich(i) for i in items], total

    async def get_upcoming(self, reference_ids: Optional[List[str]] = None, limit: int = 10) -> List[EventResponse]:
        items = await self.event_repo.get_upcoming_events(reference_ids, limit)
        return [await self._enrich(i) for i in items]

    async def update(self, event_id: str, data: EventUpdate) -> EventResponse:
        res = await self.event_repo.find_by_id(event_id)
        if not res:
            raise ValueError("Event not found")
        update_doc = data.model_dump(exclude_none=True)
        update_doc["updated_at"] = datetime.utcnow()
        updated = await self.event_repo.update(event_id, update_doc)
        return await self._enrich(updated)  # type: ignore

    async def delete(self, event_id: str) -> None:
        res = await self.event_repo.find_by_id(event_id)
        if not res:
            raise ValueError("Event not found")
        await self.event_repo.delete(event_id)
