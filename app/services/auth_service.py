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
            "school": data.school,
            "department": data.department,
            "faculty": data.faculty,
            "bio": data.bio,
            "profile_picture": "",
            "cover_photo": "",
            "skills": [],
            "interests": [],
            "followers": [],
            "following": [],
            "children": [],
            "achievements": [],
            "is_active": True,
            "is_verified": False,
            "verification_token": f"verify_{uuid.uuid4().hex}",
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

    async def forgot_password(self, email: str) -> str:
        user = await self.user_repo.find_by_email(email)
        if not user:
            raise ValueError("User not found")
        reset_token = f"reset_{uuid.uuid4().hex}"
        await self.user_repo.update(user["id"], {"reset_token": reset_token})
        return reset_token

    async def reset_password(self, token: str, new_password: str) -> None:
        db = self.user_repo.collection
        user_doc = await db.find_one({"reset_token": token})
        if not user_doc:
            raise ValueError("Invalid or expired reset token")
        user_id = str(user_doc["_id"])
        await self.user_repo.update(user_id, {
            "hashed_password": hash_password(new_password),
            "reset_token": None
        })

    async def verify_email(self, token: str) -> None:
        db = self.user_repo.collection
        user_doc = await db.find_one({"verification_token": token})
        if not user_doc:
            # Fallback check
            try:
                from bson import ObjectId
                user_doc = await db.find_one({"_id": ObjectId(token)})
            except Exception:
                pass
        if not user_doc:
            raise ValueError("Invalid verification token")
        user_id = str(user_doc["_id"])
        await self.user_repo.update(user_id, {
            "is_verified": True,
            "verification_token": None
        })

    @staticmethod
    def _tokens(user_id: str, role: str) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user_id, role),
            refresh_token=create_refresh_token(user_id),
        )
