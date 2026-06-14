from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel

from app.models.enums import NotificationType


class NotificationResponse(BaseModel):
    id: str
    notification_type: NotificationType
    title: str
    message: str
    data: dict
    is_read: bool
    created_at: datetime
