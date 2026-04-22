from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.enrollment import Enrollment


class EnrollmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, enrollment: Enrollment) -> Enrollment:
        self.db.add(enrollment)
        self.db.flush()
        return enrollment

    def get_by_user_and_course(self, user_id: UUID, course_id: UUID) -> Enrollment | None:
        stmt = select(Enrollment).where(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
        return self.db.scalar(stmt)

    def list_by_user(self, user_id: UUID) -> list[Enrollment]:
        stmt = select(Enrollment).where(Enrollment.user_id == user_id).order_by(Enrollment.enrolled_at.desc())
        return list(self.db.scalars(stmt))

    def list_by_course(self, course_id: UUID) -> list[Enrollment]:
        stmt = (
            select(Enrollment)
            .where(Enrollment.course_id == course_id)
            .options(joinedload(Enrollment.user))
            .order_by(Enrollment.enrolled_at.desc())
        )
        return list(self.db.scalars(stmt))

    def delete(self, enrollment: Enrollment) -> None:
        self.db.delete(enrollment)
