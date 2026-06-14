import hashlib
import time
from typing import Any, Optional

from app.core.redis import cache_get, cache_set


class AICache:
    @staticmethod
    def _key(prefix: str, content: str) -> str:
        digest = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"ai:{prefix}:{digest}"

    async def get_embedding(self, text: str) -> Optional[list[float]]:
        return await cache_get(self._key("emb", text))

    async def set_embedding(self, text: str, embedding: list[float], ttl: int = 86400) -> None:
        await cache_set(self._key("emb", text), embedding, ttl)

    async def get_response(self, prompt: str) -> Optional[dict]:
        return await cache_get(self._key("resp", prompt))

    async def set_response(self, prompt: str, response: dict, ttl: int = 3600) -> None:
        await cache_set(self._key("resp", prompt), response, ttl)

    async def get_prompt(self, key: str) -> Optional[str]:
        return await cache_get(self._key("prompt", key))

    async def set_prompt(self, key: str, prompt: str, ttl: int = 3600) -> None:
        await cache_set(self._key("prompt", key), prompt, ttl)


ai_cache = AICache()


class PerformanceTracker:
    def __init__(self) -> None:
        self.start = time.perf_counter()
        self.db_time_ms = 0.0
        self.embedding_time_ms = 0.0
        self.ai_time_ms = 0.0

    def add_db(self, ms: float) -> None:
        self.db_time_ms += ms

    def add_embedding(self, ms: float) -> None:
        self.embedding_time_ms += ms

    def add_ai(self, ms: float) -> None:
        self.ai_time_ms += ms

    def to_dict(self) -> dict[str, Any]:
        total = (time.perf_counter() - self.start) * 1000
        return {
            "database_query_time_ms": round(self.db_time_ms, 2),
            "embedding_time_ms": round(self.embedding_time_ms, 2),
            "ai_processing_time_ms": round(self.ai_time_ms, 2),
            "total_response_time_ms": round(total, 2),
        }
