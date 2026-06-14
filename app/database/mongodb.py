from typing import Optional
from urllib.parse import urlparse

from app.core.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

settings = get_settings()
_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    global _client, _db
    uri = settings.MONGODB_URI
    parsed = urlparse(uri)
    host = parsed.netloc or uri

    print(f"Connecting to MongoDB at {host}...")
    _client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10000)
    _db = _client[settings.MONGODB_DB]

    try:
        await _client.admin.command("ping")
        print("✅ Connected to MongoDB successfully")
    except Exception as e:
        # Don't crash the app — let it start and return 503 on DB-dependent routes
        print(f"⚠️  WARNING: Could not reach MongoDB at '{host}': {e}")
        print(
            "   The API will start, but database operations will fail until MongoDB is reachable."
        )
        print("   Fix options:")
        print(
            "     • Local:  install & start MongoDB Community → https://www.mongodb.com/try/download/community"
        )
        print(
            "     • Cloud:  create a free Atlas cluster → https://www.mongodb.com/cloud/atlas"
        )
        print("     • Then set MONGODB_URI in backend/.env and restart.")


async def close_mongo_connection() -> None:
    global _client, _db
    if _client:
        _client.close()
    _client = None
    _db = None


def get_database() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError(
            "Database not initialized. MongoDB connection was never established."
        )
    return _db
