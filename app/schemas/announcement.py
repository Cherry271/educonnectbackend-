from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import AnnouncementType, PriorityLevel


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=5)
    announcement_type: AnnouncementType = AnnouncementType.ANNOUNCEMENT
    priority: PriorityLevel = PriorityLevel.MEDIUM
    department: str = ""
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class AnnouncementResponse(BaseModel):
    id: str
    author_id: str
    author_name: str = ""
    title: str
    content: str
    announcement_type: AnnouncementType
    priority: PriorityLevel
    department: str
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
