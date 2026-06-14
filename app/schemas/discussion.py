from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DiscussionCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=10)
    tags: List[str] = []
    department: str = ""
    resource_ids: List[str] = []


class DiscussionResponse(BaseModel):
    id: str
    author_id: str
    author_name: str = ""
    title: str
    content: str
    tags: List[str]
    department: str
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False
    is_pinned: bool = False
    trending_score: float = 0
    views: int = 0
    created_at: datetime


class DiscussionCommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    parent_id: Optional[str] = None
