from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import AIResponse


class StudyAssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    resource_ids: List[str] = []
    conversation_history: List[dict] = []


class StudyAssistantResponse(AIResponse):
    suggested_resources: List[str] = []
    suggested_discussions: List[str] = []


class QuizRequest(BaseModel):
    topic: str
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: str = "intermediate"


class FlashcardRequest(BaseModel):
    topic: str
    num_cards: int = Field(default=10, ge=1, le=50)


class StudyPlanRequest(BaseModel):
    subject: str
    duration_days: int = Field(default=7, ge=1, le=90)
    hours_per_day: float = Field(default=2, ge=0.5, le=12)


class SummarizeRequest(BaseModel):
    resource_id: str
