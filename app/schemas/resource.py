from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ResourceCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = ""
    course: str = ""
    department: str = ""
    tags: List[str] = []


class ResourceResponse(BaseModel):
    id: str
    title: str
    description: str
    course: str
    department: str
    tags: List[str]
    file_url: str
    file_type: str
    file_size: int
    uploader_id: str
    uploader_name: str = ""
    downloads: int
    views: int
    avg_rating: float
    is_bookmarked: bool = False
    ai_summary: str = ""
    ai_key_concepts: List[str] = []
    ai_keywords: List[str] = []
    ai_topics: List[str] = []
    ai_difficulty: str = ""
    created_at: datetime


class ResourceRating(BaseModel):
    rating: float = Field(ge=1, le=5)
    review: str = ""
