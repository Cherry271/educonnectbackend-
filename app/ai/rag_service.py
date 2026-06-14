import time
from typing import Any

from app.ai.cache import PerformanceTracker
from app.ai.embedding_service import embedding_service
from app.ai.groq_client import groq_client as claude_client
from app.database.mongodb import get_database
from app.schemas.common import ModerationResult


class RAGService:
    CHUNK_SIZE = 500

    def chunk_text(self, text: str) -> list[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.CHUNK_SIZE):
            chunks.append(" ".join(words[i : i + self.CHUNK_SIZE]))
        return chunks or [text]

    async def index_resource(self, resource_id: str, text: str) -> None:
        db = get_database()
        await db.embeddings.delete_many({"resource_id": resource_id})
        chunks = self.chunk_text(text)
        for idx, chunk in enumerate(chunks):
            embedding = await embedding_service.embed_text(chunk)
            await db.embeddings.insert_one(
                {
                    "resource_id": resource_id,
                    "chunk_index": idx,
                    "text": chunk,
                    "embedding": embedding,
                }
            )

    async def search(
        self, query: str, limit: int = 5, resource_ids: list[str] | None = None
    ) -> list[dict]:
        tracker = PerformanceTracker()
        db_start = time.perf_counter()

        # Gracefully skip DB lookup if not initialised yet
        docs: list[dict] = []
        try:
            db = get_database()
            filter_query: dict[str, Any] = {}
            if resource_ids:
                filter_query["resource_id"] = {"$in": resource_ids}
            docs = await db.embeddings.find(filter_query).to_list(1000)
        except Exception:
            pass  # No embeddings available — AI will answer without RAG context
        tracker.add_db((time.perf_counter() - db_start) * 1000)

        if not docs:
            return []

        emb_start = time.perf_counter()
        query_embedding = await embedding_service.embed_text(query)
        tracker.add_embedding((time.perf_counter() - emb_start) * 1000)

        scored = []
        for doc in docs:
            score = embedding_service.cosine_similarity(
                query_embedding, doc.get("embedding", [])
            )
            scored.append(
                {"text": doc["text"], "resource_id": doc["resource_id"], "score": score}
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    async def generate_with_context(
        self, query: str, resource_ids: list[str] | None = None
    ) -> dict[str, Any]:
        tracker = PerformanceTracker()
        contexts = await self.search(query, limit=5, resource_ids=resource_ids)
        context_text = "\n\n".join(c["text"] for c in contexts)

        system = (
            "You are EduConnect AI, an educational assistant for a university social platform. "
            "Answer using the provided context from uploaded resources, discussions, and announcements. "
            "Be accurate, educational, and cite concepts clearly."
        )
        prompt = f"Context:\n{context_text}\n\nQuestion: {query}"

        ai_start = time.perf_counter()
        result = await claude_client.generate(prompt, system=system)
        tracker.add_ai(result["response_time_ms"])

        result["performance"] = tracker.to_dict()
        result["sources"] = [c["resource_id"] for c in contexts]
        return result


rag_service = RAGService()
