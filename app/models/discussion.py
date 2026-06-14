from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class DiscussionComment(BaseModel):
    id: str = Field(default_factory=lambda: "")
    author_id: str
    content: str
    likes: list[str] = Field(default_factory=list)
    replies: list["DiscussionComment"] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DiscussionModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    author_id: str
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    department: str = ""
    likes: list[str] = Field(default_factory=list)
    comments: list[DiscussionComment] = Field(default_factory=list)
    is_pinned: bool = False
    trending_score: float = 0.0
    views: int = 0
    resource_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
