from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course_collaborator import CourseCollaborator, CourseCollaboratorStatus


class CourseCollaboratorRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, collaborator: CourseCollaborator) -> CourseCollaborator:
        self.db.add(collaborator)
        self.db.flush()
        return collaborator

    def get_by_course_and_user(self, course_id: UUID, user_id: UUID) -> CourseCollaborator | None:
        stmt = select(CourseCollaborator).where(
            CourseCollaborator.course_id == course_id,
            CourseCollaborator.user_id == user_id,
        )
        return self.db.scalar(stmt)

    def list_by_course(
        self, course_id: UUID, *, status: CourseCollaboratorStatus | None = None
    ) -> list[CourseCollaborator]:
        stmt = select(CourseCollaborator).where(CourseCollaborator.course_id == course_id)
        if status is not None:
            stmt = stmt.where(CourseCollaborator.status == status)
        stmt = stmt.order_by(CourseCollaborator.created_at.desc())
        return list(self.db.scalars(stmt))

    def list_by_user(
        self, user_id: UUID, *, status: CourseCollaboratorStatus | None = None
    ) -> list[CourseCollaborator]:
        stmt = select(CourseCollaborator).where(CourseCollaborator.user_id == user_id)
        if status is not None:
            stmt = stmt.where(CourseCollaborator.status == status)
        stmt = stmt.order_by(CourseCollaborator.created_at.desc())
        return list(self.db.scalars(stmt))
