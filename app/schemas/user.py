from datetime import datetime
from typing import List, Optional

from app.models.enums import UserRole
from pydantic import BaseModel, EmailStr, Field


class UserPublic(BaseModel):
    id: str
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    role: UserRole
    school: str = ""
    department: str
    faculty: str
    bio: str
    profile_picture: str
    cover_photo: str
    skills: List[str]
    interests: List[str]
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    resources_count: int = 0
    children: List[str] = []
    achievements: List[dict]
    created_at: datetime


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    school: Optional[str] = None
    department: Optional[str] = None
    faculty: Optional[str] = None
    skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    profile_picture: Optional[str] = None
    cover_photo: Optional[str] = None
    children: Optional[List[str]] = None


class ProfileAnalytics(BaseModel):
    followers_growth: int
    posts_this_month: int
    resources_uploaded: int
    discussions_joined: int
    engagement_rate: float
    average_quiz_score: float = 0.0
    resources_accessed: int = 0
    study_time_hours: int = 0
    rank: str = "Top 20%"
    rank_change: str = "Stable"
    quiz_change: str = "+0.0%"
    resources_change: str = "+0"
    study_change: str = "+0h"


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class NotificationSettings(BaseModel):
    email_notifications: bool = True
    push_notifications: bool = True
    message_notifications: bool = True
    group_notifications: bool = True
    announcement_notifications: bool = True
    discussion_notifications: bool = True
    follow_notifications: bool = True
    like_notifications: bool = True
