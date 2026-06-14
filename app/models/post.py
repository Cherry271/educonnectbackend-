from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.enums import PostType


class CommentModel(BaseModel):
    id: str = Field(default_factory=lambda: "")
    author_id: str
    content: str
    likes: list[str] = Field(default_factory=list)
    replies: list["CommentModel"] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PostModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    author_id: str
    content: str = ""
    post_type: PostType = PostType.TEXT
    media_url: str = ""
    media_metadata: dict[str, Any] = Field(default_factory=dict)
    resource_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    department: str = ""
    likes: list[str] = Field(default_factory=list)
    comments: list[CommentModel] = Field(default_factory=list)
    shares: list[str] = Field(default_factory=list)
    bookmarks: list[str] = Field(default_factory=list)
    reports: list[dict[str, Any]] = Field(default_factory=list)
    is_edited: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
