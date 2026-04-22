from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course


class CourseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, course: Course) -> Course:
        self.db.add(course)
        self.db.flush()
        return course

    def get_by_id(self, course_id: UUID) -> Course | None:
        return self.db.get(Course, course_id)

    def list_all(self) -> list[Course]:
        stmt = select(Course).order_by(Course.created_at.desc())
        return list(self.db.scalars(stmt))

    def list_by_author(self, author_id: UUID) -> list[Course]:
        stmt = select(Course).where(Course.author_id == author_id).order_by(Course.created_at.desc())
        return list(self.db.scalars(stmt))

    def delete(self, course: Course) -> None:
        self.db.delete(course)
