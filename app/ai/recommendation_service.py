import json

from app.ai.groq_client import groq_client as claude_client
from app.repositories.discussion_repo import DiscussionRepository
from app.repositories.resource_repo import ResourceRepository
from app.repositories.user_repo import UserRepository


class SummarizationService:
    async def summarize_resource(self, title: str, text: str) -> dict:
        prompt = (
            f"Summarize this educational resource. Return JSON only with keys: "
            f"summary, key_concepts (list), keywords (list), topics (list), difficulty (beginner|intermediate|advanced)\n\n"
            f"Title: {title}\n\nContent:\n{text[:8000]}"
        )
        result = await claude_client.generate(
            prompt, system="You are an educational content analyzer."
        )

        try:
            return json.loads(result["response"])
        except json.JSONDecodeError:
            return {
                "summary": result["response"][:500],
                "key_concepts": [],
                "keywords": title.split()[:5],
                "topics": [],
                "difficulty": "intermediate",
            }


summarization_service = SummarizationService()


class RecommendationService:
    def __init__(self) -> None:
        self.user_repo = UserRepository()
        self.resource_repo = ResourceRepository()
        self.discussion_repo = DiscussionRepository()

    async def recommend_resources(self, user: dict, limit: int = 5) -> list[dict]:
        department = user.get("department", "")
        interests = user.get("interests", [])
        query = department or (interests[0] if interests else "education")
        return await self.resource_repo.search(query, limit=limit)

    async def recommend_discussions(self, user: dict, limit: int = 5) -> list[dict]:
        return await self.discussion_repo.get_trending(limit=limit)

    async def recommend_groups(self, user: dict, limit: int = 5) -> list[dict]:
        from app.repositories.group_repo import GroupRepository

        repo = GroupRepository()
        dept = user.get("department", "")
        return await repo.search(dept or "study", limit=limit)

    async def recommend_friends(self, user: dict, limit: int = 5) -> list[dict]:
        department = user.get("department", "")
        following = set(user.get("following", []))
        following.add(user["id"])
        db = self.user_repo.collection
        cursor = db.find({"department": department, "_id": {"$nin": []}}).limit(
            limit + len(following)
        )
        docs = await cursor.to_list(limit + len(following))
        results = []
        for doc in docs:
            uid = str(doc["_id"])
            if uid not in following:
                results.append(self.user_repo.serialize(doc))
            if len(results) >= limit:
                break
        return results


recommendation_service = RecommendationService()
