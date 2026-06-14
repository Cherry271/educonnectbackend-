from typing import List, Optional

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    q: str = Field(min_length=1, max_length=200)
    type: Optional[str] = None  # people, resources, discussions, announcements, groups
    page: int = 1
    page_size: int = 20


class SearchResult(BaseModel):
    id: str
    type: str
    title: str
    snippet: str
    score: float = 0
    metadata: dict = {}
