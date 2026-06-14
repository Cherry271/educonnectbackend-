import os
import uuid
from datetime import datetime
from typing import Optional

import aiofiles

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

settings = get_settings()


class AuthService:
    def __init__(self) -> None:
        self.user_repo = UserRepository()

    async def register(self, data: RegisterRequest) -> TokenResponse:
        if await self.user_repo.find_by_email(data.email):
            raise ValueError("Email already registered")
        if await self.user_repo.find_by_username(data.username):
            raise ValueError("Username already taken")

        user_doc = {
            "first_name": data.first_name,
            "last_name": data.last_name,
            "username": data.username.lower(),
            "email": data.email.lower(),
            "hashed_password": hash_password(data.password),
            "role": data.role.value,
            "department": data.department,
            "faculty": data.faculty,
            "bio": data.bio,
            "profile_picture": "",
            "cover_photo": "",
            "skills": [],
            "interests": [],
            "followers": [],
            "following": [],
            "achievements": [],
            "is_active": True,
            "is_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        user = await self.user_repo.create(user_doc)
        return self._tokens(user["id"], user["role"])

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.user_repo.find_by_identifier(data.identifier)
        if not user or not verify_password(data.password, user["hashed_password"]):
            raise ValueError("Invalid credentials")
        if not user.get("is_active", True):
            raise ValueError("Account disabled")
        return self._tokens(user["id"], user["role"])

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = verify_token(refresh_token, refresh=True)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")
        user = await self.user_repo.find_by_id(payload["sub"])
        if not user:
            raise ValueError("User not found")
        return self._tokens(user["id"], user["role"])

    @staticmethod
    def _tokens(user_id: str, role: str) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user_id, role),
            refresh_token=create_refresh_token(user_id),
        )
