from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    content: str = ""
    file_url: str = ""
    voice_url: str = ""
    message_type: str = "text"


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    sender_name: str = ""
    content: str
    file_url: str
    voice_url: str
    message_type: str
    read_by: List[str]
    created_at: datetime


class ConversationCreate(BaseModel):
    participant_ids: List[str] = Field(min_length=1)
    is_group: bool = False
    group_name: str = ""


class ConversationResponse(BaseModel):
    id: str
    participants: List[str]
    participant_names: List[str] = []
    is_group: bool
    group_name: str
    last_message: str
    last_message_at: datetime
    unread_count: int = 0
