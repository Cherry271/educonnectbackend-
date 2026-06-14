from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ResourceModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    title: str
    description: str = ""
    course: str = ""
    department: str = ""
    tags: list[str] = Field(default_factory=list)
    file_url: str = ""
    file_type: str = ""
    file_size: int = 0
    uploader_id: str
    downloads: int = 0
    views: int = 0
    ratings: list[dict[str, Any]] = Field(default_factory=list)
    avg_rating: float = 0.0
    bookmarks: list[str] = Field(default_factory=list)
    comments: list[dict[str, Any]] = Field(default_factory=list)
    ai_summary: str = ""
    ai_key_concepts: list[str] = Field(default_factory=list)
    ai_keywords: list[str] = Field(default_factory=list)
    ai_topics: list[str] = Field(default_factory=list)
    ai_difficulty: str = "intermediate"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
