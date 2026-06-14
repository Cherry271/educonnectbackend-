import json
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()
_redis: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def cache_get(key: str) -> Optional[Any]:
    try:
        client = await get_redis()
        value = await client.get(key)
        return json.loads(value) if value else None
    except Exception:
        return None


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    try:
        client = await get_redis()
        await client.set(key, json.dumps(value, default=str), ex=ttl or settings.CACHE_TTL_SECONDS)
    except Exception:
        pass


async def cache_delete(key: str) -> None:
    try:
        client = await get_redis()
        await client.delete(key)
    except Exception:
        pass
