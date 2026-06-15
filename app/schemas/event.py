from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = ""
    start_time: datetime
    end_time: datetime
    event_type: str = "event"  # exam, deadline, activity, event
    reference_id: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_type: Optional[str] = None
    reference_id: Optional[str] = None


class EventResponse(BaseModel):
    id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    event_type: str
    reference_id: Optional[str] = None
    created_by: str
    created_at: datetime
