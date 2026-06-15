from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AssignmentModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    title: str
    description: str = ""
    instructions_url: str = ""
    course_id: str = ""  # Can link to a group/course
    deadline: datetime
    max_score: float = 100.0
    created_by: str  # Teacher ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class SubmissionModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    assignment_id: str
    student_id: str
    document_url: str = ""
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "submitted"  # submitted, graded

    class Config:
        populate_by_name = True


class GradeModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    submission_id: str
    score: float
    feedback: str = ""
    graded_by: str  # Teacher ID
    graded_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
