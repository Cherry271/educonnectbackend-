from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


class UserModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    hashed_password: str
    role: UserRole = UserRole.STUDENT
    department: str = ""
    faculty: str = ""
    bio: str = ""
    profile_picture: str = ""
    cover_photo: str = ""
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    followers: list[str] = Field(default_factory=list)
    following: list[str] = Field(default_factory=list)
    achievements: list[dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
