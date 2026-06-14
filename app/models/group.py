from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import GroupType


class GroupModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    description: str = ""
    group_type: GroupType = GroupType.STUDY
    department: str = ""
    course: str = ""
    creator_id: str
    members: list[str] = Field(default_factory=list)
    moderators: list[str] = Field(default_factory=list)
    invited: list[str] = Field(default_factory=list)
    cover_image: str = ""
    is_private: bool = False
    resource_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
