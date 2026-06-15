from app.repositories.base import BaseRepository


class AssignmentRepository(BaseRepository):
    collection_name = "assignments"


class SubmissionRepository(BaseRepository):
    collection_name = "submissions"

    async def find_by_student_and_assignment(self, student_id: str, assignment_id: str) -> list[dict]:
        cursor = self.collection.find({"student_id": student_id, "assignment_id": assignment_id})
        docs = await cursor.to_list(100)
        return [self.serialize(d) for d in docs if d]


class GradeRepository(BaseRepository):
    collection_name = "grades"

    async def find_by_submission(self, submission_id: str) -> dict | None:
        doc = await self.collection.find_one({"submission_id": submission_id})
        return self.serialize(doc)
