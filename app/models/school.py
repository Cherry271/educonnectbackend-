from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SchoolModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    address: str = ""
    website: str = ""
    domain: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
