import time
from typing import Optional

import numpy as np

from app.ai.cache import ai_cache
from app.core.config import get_settings

settings = get_settings()
_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception:
            _model = "mock"
    return _model


class EmbeddingService:
    async def embed_text(self, text: str) -> list[float]:
        cached = await ai_cache.get_embedding(text)
        if cached:
            return cached

        start = time.perf_counter()
        model = _get_model()

        if model == "mock":
            np.random.seed(hash(text) % 2**32)
            embedding = np.random.randn(384).tolist()
        else:
            embedding = model.encode(text).tolist()

        await ai_cache.set_embedding(text, embedding)
        elapsed = (time.perf_counter() - start) * 1000
        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed_text(t) for t in texts]

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        va, vb = np.array(a), np.array(b)
        denom = np.linalg.norm(va) * np.linalg.norm(vb)
        if denom == 0:
            return 0.0
        return float(np.dot(va, vb) / denom)


embedding_service = EmbeddingService()
