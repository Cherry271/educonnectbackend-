from datetime import datetime
from typing import Optional, List, Tuple
from app.repositories.assignment_repo import AssignmentRepository, SubmissionRepository, GradeRepository
from app.repositories.user_repo import UserRepository
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentResponse,
    SubmissionCreate,
    SubmissionResponse,
    GradeCreate,
    GradeResponse,
)
from app.services.notification_service import NotificationService
from app.models.enums import NotificationType


class AssignmentService:
    def __init__(self) -> None:
        self.assignment_repo = AssignmentRepository()
        self.submission_repo = SubmissionRepository()
        self.grade_repo = GradeRepository()
        self.user_repo = UserRepository()
        self.notification_service = NotificationService()

    async def _enrich_assignment(self, doc: dict) -> AssignmentResponse:
        return AssignmentResponse(
            id=doc["id"],
            title=doc["title"],
            description=doc.get("description", ""),
            instructions_url=doc.get("instructions_url", ""),
            course_id=doc.get("course_id", ""),
            deadline=doc["deadline"],
            max_score=doc.get("max_score", 100.0),
            created_by=doc["created_by"],
            created_at=doc.get("created_at", datetime.utcnow()),
        )

    async def _enrich_submission(self, doc: dict) -> SubmissionResponse:
        grade_doc = await self.grade_repo.find_by_submission(doc["id"])
        return SubmissionResponse(
            id=doc["id"],
            assignment_id=doc["assignment_id"],
            student_id=doc["student_id"],
            document_url=doc.get("document_url", ""),
            submitted_at=doc.get("submitted_at", datetime.utcnow()),
            status=doc.get("status", "submitted"),
            grade=grade_doc,
        )

    async def create_assignment(self, teacher_id: str, data: AssignmentCreate) -> AssignmentResponse:
        doc = {
            **data.model_dump(),
            "created_by": teacher_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        res = await self.assignment_repo.create(doc)
        return await self._enrich_assignment(res)

    async def get_assignment(self, assignment_id: str) -> AssignmentResponse:
        res = await self.assignment_repo.find_by_id(assignment_id)
        if not res:
            raise ValueError("Assignment not found")
        return await self._enrich_assignment(res)

    async def list_assignments(self, course_id: Optional[str] = None, page: int = 1, page_size: int = 20) -> Tuple[List[AssignmentResponse], int]:
        filter_q = {}
        if course_id:
            filter_q["course_id"] = course_id
        items, total = await self.assignment_repo.paginate(filter_q, page, page_size, sort=[("created_at", -1)])
        res = [await self._enrich_assignment(i) for i in items]
        return res, total

    async def submit_assignment(self, student_id: str, assignment_id: str, data: SubmissionCreate) -> SubmissionResponse:
        # Check if assignment exists
        assignment = await self.assignment_repo.find_by_id(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")

        # Create submission doc
        doc = {
            "assignment_id": assignment_id,
            "student_id": student_id,
            "document_url": data.document_url,
            "status": "submitted",
            "submitted_at": datetime.utcnow(),
        }
        res = await self.submission_repo.create(doc)

        # Notify the teacher
        await self.notification_service.create(
            user_id=assignment["created_by"],
            notification_type=NotificationType.RESOURCE,  # Use RESOURCE or custom
            title="Assignment Submission",
            message=f"A student submitted their work for: {assignment['title']}",
            data={"assignment_id": assignment_id, "submission_id": res["id"]},
        )

        return await self._enrich_submission(res)

    async def get_submission(self, submission_id: str) -> SubmissionResponse:
        res = await self.submission_repo.find_by_id(submission_id)
        if not res:
            raise ValueError("Submission not found")
        return await self._enrich_submission(res)

    async def list_submissions(self, assignment_id: str, page: int = 1, page_size: int = 20) -> Tuple[List[SubmissionResponse], int]:
        filter_q = {"assignment_id": assignment_id}
        items, total = await self.submission_repo.paginate(filter_q, page, page_size, sort=[("submitted_at", -1)])
        res = [await self._enrich_submission(i) for i in items]
        return res, total

    async def get_student_submissions(self, student_id: str) -> List[SubmissionResponse]:
        db = self.submission_repo.collection
        cursor = db.find({"student_id": student_id})
        docs = await cursor.to_list(100)
        return [await self._enrich_submission(self.submission_repo.serialize(d)) for d in docs if d]

    async def grade_submission(self, teacher_id: str, submission_id: str, data: GradeCreate) -> SubmissionResponse:
        submission = await self.submission_repo.find_by_id(submission_id)
        if not submission:
            raise ValueError("Submission not found")

        # Update submission status
        await self.submission_repo.update(submission_id, {"status": "graded"})

        # Check if already graded, update or create
        existing_grade = await self.grade_repo.find_by_submission(submission_id)
        grade_doc = {
            "submission_id": submission_id,
            "score": data.score,
            "feedback": data.feedback,
            "graded_by": teacher_id,
            "graded_at": datetime.utcnow(),
        }

        if existing_grade:
            await self.grade_repo.update(existing_grade["id"], grade_doc)
        else:
            await self.grade_repo.create(grade_doc)

        # Notify student
        assignment = await self.assignment_repo.find_by_id(submission["assignment_id"])
        assignment_title = assignment["title"] if assignment else "Assignment"
        await self.notification_service.create(
            user_id=submission["student_id"],
            notification_type=NotificationType.ANNOUNCEMENT,
            title="Assignment Graded",
            message=f"Your submission for '{assignment_title}' has been graded. Score: {data.score}",
            data={"assignment_id": submission["assignment_id"], "submission_id": submission_id},
        )

        # Re-fetch and return enriched submission
        updated_sub = await self.submission_repo.find_by_id(submission_id)
        return await self._enrich_submission(updated_sub)  # type: ignore
