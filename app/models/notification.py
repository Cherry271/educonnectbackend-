from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.enums import NotificationType


class NotificationModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
