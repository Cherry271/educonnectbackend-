from datetime import datetime
from typing import Any, List, Optional

from app.models.enums import GroupType
from pydantic import BaseModel, Field


class GroupCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str = ""
    group_type: GroupType = GroupType.STUDY
    department: str = ""
    course: str = ""
    is_private: bool = False


class GroupResponse(BaseModel):
    id: str
    name: str
    description: str
    group_type: GroupType
    department: str
    course: str
    creator_id: str
    members_count: int = 0
    is_member: bool = False
    is_private: bool
    cover_image: str = ""
    conversation_id: Optional[str] = None
    created_at: datetime


class GroupInvite(BaseModel):
    user_ids: List[str]
