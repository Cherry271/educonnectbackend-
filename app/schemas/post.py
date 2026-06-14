from datetime import datetime
from typing import List, Optional

from app.models.enums import PostType
from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    parent_id: Optional[str] = None


class CommentResponse(BaseModel):
    id: str
    author_id: str
    author_name: str = ""
    author_avatar: str = ""
    content: str
    likes_count: int = 0
    is_liked: bool = False
    replies: List["CommentResponse"] = []
    created_at: datetime


class PostCreate(BaseModel):
    content: str = ""
    post_type: PostType = PostType.TEXT
    media_url: str = ""
    resource_id: Optional[str] = None
    poll_question: str = ""
    poll_options: List[str] = []
    tags: List[str] = []
    department: str = ""


class PostUpdate(BaseModel):
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class PostResponse(BaseModel):
    id: str
    author_id: str
    author_name: str = ""
    author_avatar: str = ""
    author_role: str = ""
    author_department: str = ""
    content: str
    post_type: PostType
    media_url: str
    resource_id: Optional[str] = None
    poll_question: str = ""
    poll_options: List[str] = []
    tags: List[str]
    department: str
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    is_liked: bool = False
    is_bookmarked: bool = False
    comments: List[CommentResponse] = []
    is_edited: bool = False
    created_at: datetime
    updated_at: datetime


class ReportPostRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=500)
