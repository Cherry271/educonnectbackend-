import json

from app.ai.groq_client import groq_client as claude_client
from app.ai.rag_service import rag_service
from app.ai.recommendation_service import recommendation_service
from app.schemas.ai import FlashcardRequest, QuizRequest, StudyPlanRequest


class StudyAssistantService:
    SYSTEM_PROMPT = (
        "You are EduConnect AI — an intelligent study assistant for university students and teachers. "
        "Help with academic questions, explain concepts, and guide learning using platform resources."
    )

    async def chat(
        self, message: str, user: dict, resource_ids: list[str] | None = None
    ) -> dict:
        result = await rag_service.generate_with_context(
            message, resource_ids=resource_ids
        )
        # Recommendations are non-critical — skip on error (e.g. empty DB)
        try:
            resources = await recommendation_service.recommend_resources(user, limit=3)
            result["suggested_resources"] = [r["id"] for r in resources]
        except Exception:
            result["suggested_resources"] = []
        try:
            discussions = await recommendation_service.recommend_discussions(
                user, limit=3
            )
            result["suggested_discussions"] = [d["id"] for d in discussions]
        except Exception:
            result["suggested_discussions"] = []
        return result

    async def generate_quiz(self, request: QuizRequest) -> dict:
        prompt = (
            f'Generate {request.num_questions} {request.difficulty} quiz questions about "{request.topic}". '
            f'Return JSON: {{"questions":[{{"question":"","options":["A","B","C","D"],"answer":"A","explanation":""}}]}}'
        )
        return await claude_client.generate(prompt, system=self.SYSTEM_PROMPT)

    async def generate_flashcards(self, request: FlashcardRequest) -> dict:
        prompt = (
            f'Generate {request.num_cards} flashcards about "{request.topic}". '
            f'Return JSON: {{"cards":[{{"front":"","back":""}}]}}'
        )
        return await claude_client.generate(prompt, system=self.SYSTEM_PROMPT)

    async def generate_study_plan(self, request: StudyPlanRequest) -> dict:
        prompt = (
            f'Create a {request.duration_days}-day study plan for "{request.subject}" '
            f"with {request.hours_per_day} hours/day. "
            f'Return JSON: {{"plan":[{{"day":1,"topics":[],"activities":[],"hours":2}}]}}'
        )
        return await claude_client.generate(prompt, system=self.SYSTEM_PROMPT)


study_assistant = StudyAssistantService()
