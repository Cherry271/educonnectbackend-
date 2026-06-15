from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class EventModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    title: str
    description: str = ""
    start_time: datetime
    end_time: datetime
    event_type: str = "event"  # exam, deadline, activity, event
    reference_id: Optional[str] = None  # Link to group, course or school
    created_by: str  # User ID of creator
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
