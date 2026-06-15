from datetime import datetime
from app.repositories.school_repo import SchoolRepository
from app.schemas.school import SchoolCreate, SchoolUpdate, SchoolResponse


class SchoolService:
    def __init__(self) -> None:
        self.school_repo = SchoolRepository()

    async def _enrich(self, school: dict) -> SchoolResponse:
        return SchoolResponse(
            id=school["id"],
            name=school["name"],
            address=school.get("address", ""),
            website=school.get("website", ""),
            domain=school.get("domain", ""),
            created_at=school.get("created_at", datetime.utcnow()),
            updated_at=school.get("updated_at", datetime.utcnow()),
        )

    async def create(self, data: SchoolCreate) -> SchoolResponse:
        existing = await self.school_repo.find_by_name(data.name)
        if existing:
            raise ValueError("School with this name already exists")
        doc = {
            **data.model_dump(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        school = await self.school_repo.create(doc)
        return await self._enrich(school)

    async def get(self, school_id: str) -> SchoolResponse:
        school = await self.school_repo.find_by_id(school_id)
        if not school:
            raise ValueError("School not found")
        return await self._enrich(school)

    async def list_schools(self, page: int = 1, page_size: int = 20) -> tuple[list[SchoolResponse], int]:
        schools, total = await self.school_repo.paginate({}, page, page_size)
        return [await self._enrich(s) for s in schools], total

    async def update(self, school_id: str, data: SchoolUpdate) -> SchoolResponse:
        school = await self.school_repo.find_by_id(school_id)
        if not school:
            raise ValueError("School not found")
        update_doc = data.model_dump(exclude_none=True)
        update_doc["updated_at"] = datetime.utcnow()
        updated = await self.school_repo.update(school_id, update_doc)
        return await self._enrich(updated)  # type: ignore

    async def delete(self, school_id: str) -> None:
        school = await self.school_repo.find_by_id(school_id)
        if not school:
            raise ValueError("School not found")
        await self.school_repo.delete(school_id)
