from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import verify_token
from app.database.mongodb import get_database
from app.models.enums import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    payload = verify_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return payload["sub"]


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    user_id = await get_current_user_id(token)
    db = get_database()
    user = await db.users.find_one({"_id": __import__("bson").ObjectId(user_id)})
    if not user:
        users_in_db = [u.get("username") for u in getattr(db.users, "docs", [])]
        print(f"\n--- DEBUG: user_id={user_id} not found. Users in mock DB: {users_in_db} ---")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    user["id"] = str(user.pop("_id"))
    return user


def require_roles(*roles: UserRole):
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in [r.value for r in roles]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return checker


RequireTeacher = require_roles(UserRole.TEACHER, UserRole.ADMIN)
RequireAdmin = require_roles(UserRole.ADMIN)
