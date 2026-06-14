from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class MessageModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    conversation_id: str
    sender_id: str
    content: str = ""
    file_url: str = ""
    voice_url: str = ""
    message_type: str = "text"
    read_by: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class ConversationModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    participants: list[str] = Field(default_factory=list)
    is_group: bool = False
    group_name: str = ""
    last_message: str = ""
    last_message_at: datetime = Field(default_factory=datetime.utcnow)
    typing_users: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
