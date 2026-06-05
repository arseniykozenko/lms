from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.assignment import Assignment, AssignmentSubmission
from app.models.module import Module


class AssignmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, assignment: Assignment) -> Assignment:
        self.db.add(assignment)
        self.db.flush()
        return assignment

    def get_by_id(self, assignment_id: UUID) -> Assignment | None:
        stmt = (
            select(Assignment)
            .where(Assignment.id == assignment_id)
            .options(
                selectinload(Assignment.module).selectinload(Module.course),
                selectinload(Assignment.submissions),
                selectinload(Assignment.attachments),
            )
        )
        return self.db.scalar(stmt)

    def list_by_module(self, module_id: UUID) -> list[Assignment]:
        stmt = (
            select(Assignment)
            .where(Assignment.module_id == module_id)
            .options(selectinload(Assignment.submissions), selectinload(Assignment.attachments))
            .order_by(Assignment.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def delete(self, assignment: Assignment) -> None:
        self.db.delete(assignment)


class AssignmentSubmissionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, submission: AssignmentSubmission) -> AssignmentSubmission:
        self.db.add(submission)
        self.db.flush()
        return submission

    def get_by_id(self, submission_id: UUID) -> AssignmentSubmission | None:
        stmt = (
            select(AssignmentSubmission)
            .where(AssignmentSubmission.id == submission_id)
            .options(
                selectinload(AssignmentSubmission.assignment).selectinload(Assignment.module).selectinload(Module.course),
                selectinload(AssignmentSubmission.student),
                selectinload(AssignmentSubmission.attachments),
            )
        )
        return self.db.scalar(stmt)

    def list_for_student(self, assignment_id: UUID, student_id: UUID) -> list[AssignmentSubmission]:
        stmt = (
            select(AssignmentSubmission)
            .where(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.student_id == student_id,
            )
            .options(
                selectinload(AssignmentSubmission.assignment),
                selectinload(AssignmentSubmission.student),
                selectinload(AssignmentSubmission.attachments),
            )
            .order_by(AssignmentSubmission.attempt_number.desc(), AssignmentSubmission.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def get_current_for_student(self, assignment_id: UUID, student_id: UUID) -> AssignmentSubmission | None:
        stmt = (
            select(AssignmentSubmission)
            .where(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.student_id == student_id,
            )
            .options(
                selectinload(AssignmentSubmission.assignment),
                selectinload(AssignmentSubmission.student),
                selectinload(AssignmentSubmission.attachments),
            )
            .order_by(AssignmentSubmission.updated_at.desc(), AssignmentSubmission.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def list_for_assignment(self, assignment_id: UUID) -> list[AssignmentSubmission]:
        stmt = (
            select(AssignmentSubmission)
            .where(AssignmentSubmission.assignment_id == assignment_id)
            .options(
                selectinload(AssignmentSubmission.assignment),
                selectinload(AssignmentSubmission.student),
                selectinload(AssignmentSubmission.attachments),
            )
            .order_by(AssignmentSubmission.created_at.desc(), AssignmentSubmission.attempt_number.desc())
        )
        return list(self.db.scalars(stmt))

    def next_attempt_number(self, assignment_id: UUID, student_id: UUID) -> int:
        stmt = select(func.max(AssignmentSubmission.attempt_number)).where(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.student_id == student_id,
        )
        current = self.db.scalar(stmt)
        return int(current or 0) + 1

    def has_submissions(self, assignment_id: UUID) -> bool:
        stmt = select(AssignmentSubmission.id).where(AssignmentSubmission.assignment_id == assignment_id).limit(1)
        return self.db.scalar(stmt) is not None

    def delete(self, submission: AssignmentSubmission) -> None:
        self.db.delete(submission)
