from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    has_more: bool


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class PerformanceMetrics(BaseModel):
    database_query_time_ms: float = 0
    embedding_time_ms: float = 0
    ai_processing_time_ms: float = 0
    total_response_time_ms: float = 0


class AIResponse(BaseModel):
    response: str
    confidence_score: float = Field(ge=0, le=1)
    model_used: str = "Claude"
    response_time_ms: float = 0
    tokens_used: int = 0
    performance: Optional[PerformanceMetrics] = None


class ModerationResult(BaseModel):
    is_safe: bool
    confidence_score: float = Field(ge=0, le=1)
    reason: str = ""
