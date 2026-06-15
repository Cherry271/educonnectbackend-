from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AssignmentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = ""
    instructions_url: str = ""
    course_id: str = ""
    deadline: datetime
    max_score: float = 100.0


class AssignmentResponse(BaseModel):
    id: str
    title: str
    description: str
    instructions_url: str
    course_id: str
    deadline: datetime
    max_score: float
    created_by: str
    created_at: datetime


class SubmissionCreate(BaseModel):
    document_url: str


class SubmissionResponse(BaseModel):
    id: str
    assignment_id: str
    student_id: str
    document_url: str
    submitted_at: datetime
    status: str
    grade: Optional[dict] = None  # Embedded grade representation for convenience


class GradeCreate(BaseModel):
    score: float
    feedback: str = ""


class GradeResponse(BaseModel):
    id: str
    submission_id: str
    score: float
    feedback: str
    graded_by: str
    graded_at: datetime
