import os
import uuid
from datetime import datetime

import aiofiles
from app.core.config import get_settings
from app.repositories.resource_repo import ResourceRepository
from app.repositories.user_repo import UserRepository
from app.schemas.resource import ResourceCreate, ResourceResponse
from app.services.notification_service import NotificationService
from app.utils.file_extract import extract_text_from_file

settings = get_settings()


class StorageService:
    async def save_file(self, file_content: bytes, filename: str) -> str:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(filename)[1]
        unique_name = f"{uuid.uuid4()}{ext}"
        path = os.path.join(settings.UPLOAD_DIR, unique_name)
        async with aiofiles.open(path, "wb") as f:
            await f.write(file_content)
        return f"/uploads/{unique_name}"


storage_service = StorageService()


class ResourceService:
    def __init__(self) -> None:
        self.resource_repo = ResourceRepository()
        self.user_repo = UserRepository()
        self.notification_service = NotificationService()

    async def _enrich(self, resource: dict, current_user_id: str | None = None) -> ResourceResponse:
        uploader = await self.user_repo.find_by_id(resource["uploader_id"])
        bookmarks = resource.get("bookmarks", [])
        return ResourceResponse(
            id=resource["id"],
            title=resource["title"],
            description=resource.get("description", ""),
            course=resource.get("course", ""),
            department=resource.get("department", ""),
            tags=resource.get("tags", []),
            file_url=resource.get("file_url", ""),
            file_type=resource.get("file_type", ""),
            file_size=resource.get("file_size", 0),
            uploader_id=resource["uploader_id"],
            uploader_name=f"{uploader['first_name']} {uploader['last_name']}" if uploader else "",
            downloads=resource.get("downloads", 0),
            views=resource.get("views", 0),
            avg_rating=resource.get("avg_rating", 0),
            is_bookmarked=current_user_id in bookmarks if current_user_id else False,
            ai_summary=resource.get("ai_summary", ""),
            ai_key_concepts=resource.get("ai_keywords", resource.get("ai_key_concepts", [])),
            ai_keywords=resource.get("ai_keywords", []),
            ai_topics=resource.get("ai_topics", []),
            ai_difficulty=resource.get("ai_difficulty", ""),
            created_at=resource.get("created_at", datetime.utcnow()),
        )

    async def upload(
        self, uploader_id: str, data: ResourceCreate, file_content: bytes, filename: str, content_type: str
    ) -> ResourceResponse:
        file_url = await storage_service.save_file(file_content, filename)
        user = await self.user_repo.find_by_id(uploader_id)

        doc = {
            **data.model_dump(),
            "file_url": file_url,
            "file_type": content_type or os.path.splitext(filename)[1],
            "file_size": len(file_content),
            "uploader_id": uploader_id,
            "department": data.department or (user.get("department", "") if user else ""),
            "downloads": 0,
            "views": 0,
            "ratings": [],
            "avg_rating": 0,
            "bookmarks": [],
            "comments": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        resource = await self.resource_repo.create(doc)

        # Background AI processing (lazy-import; skip if AI deps unavailable)
        try:
            text = extract_text_from_file(file_content, filename)
            if text:
                try:
                    from app.ai.recommendation_service import summarization_service
                    from app.ai.rag_service import rag_service
                    summary_data = await summarization_service.summarize_resource(data.title, text)
                    await self.resource_repo.update(resource["id"], {
                        "ai_summary": summary_data.get("summary", ""),
                        "ai_key_concepts": summary_data.get("key_concepts", []),
                        "ai_keywords": summary_data.get("keywords", []),
                        "ai_topics": summary_data.get("topics", []),
                        "ai_difficulty": summary_data.get("difficulty", "intermediate"),
                    })
                    await rag_service.index_resource(resource["id"], text)
                    resource = await self.resource_repo.find_by_id(resource["id"])
                except Exception:
                    # AI components unavailable; continue without background processing
                    pass
        except Exception:
            pass

        followers = user.get("followers", []) if user else []
        for follower_id in followers[:50]:
            await self.notification_service.notify_resource(follower_id, uploader_id, resource["id"])

        return await self._enrich(resource, uploader_id)  # type: ignore

    async def list_resources(self, page: int, page_size: int, user_id: str | None = None):
        items, total = await self.resource_repo.paginate({}, page, page_size, sort=[("created_at", -1)])
        return [await self._enrich(i, user_id) for i in items], total

    async def get(self, resource_id: str, user_id: str | None = None) -> ResourceResponse:
        await self.resource_repo.increment_views(resource_id)
        resource = await self.resource_repo.find_by_id(resource_id)
        if not resource:
            raise ValueError("Resource not found")
        return await self._enrich(resource, user_id)

    async def download(self, resource_id: str) -> dict:
        await self.resource_repo.increment_downloads(resource_id)
        resource = await self.resource_repo.find_by_id(resource_id)
        if not resource:
            raise ValueError("Resource not found")
        return {"file_url": resource["file_url"], "title": resource["title"]}

    async def rate(self, resource_id: str, user_id: str, rating: float, review: str = "") -> None:
        await self.resource_repo.add_rating(resource_id, user_id, rating, review)

    async def bookmark(self, resource_id: str, user_id: str) -> bool:
        return await self.resource_repo.toggle_bookmark(resource_id, user_id)
