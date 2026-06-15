from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SchoolCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    address: str = ""
    website: str = ""
    domain: str = ""


class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    domain: Optional[str] = None


class SchoolResponse(BaseModel):
    id: str
    name: str
    address: str
    website: str
    domain: str
    created_at: datetime
    updated_at: datetime
