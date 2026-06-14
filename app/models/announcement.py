from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import AnnouncementType, PriorityLevel


class AnnouncementModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    author_id: str
    title: str
    content: str
    announcement_type: AnnouncementType = AnnouncementType.ANNOUNCEMENT
    priority: PriorityLevel = PriorityLevel.MEDIUM
    department: str = ""
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
