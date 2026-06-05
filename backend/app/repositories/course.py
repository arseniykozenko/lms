from uuid import UUID

from sqlalchemy import Select, select
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

    def list_filtered(
        self,
        *,
        query: str | None = None,
        category: str | None = None,
        is_free: bool | None = None,
    ) -> list[Course]:
        stmt: Select[tuple[Course]] = select(Course)
        if query:
            q = f"%{query.strip()}%"
            stmt = stmt.where((Course.title.ilike(q)) | (Course.description.ilike(q)))
        if category:
            stmt = stmt.where(Course.category == category)
        if is_free is not None:
            stmt = stmt.where(Course.is_free == is_free)
        stmt = stmt.order_by(Course.created_at.desc())
        return list(self.db.scalars(stmt))

    def list_by_author(self, author_id: UUID) -> list[Course]:
        stmt = select(Course).where(Course.author_id == author_id).order_by(Course.created_at.desc())
        return list(self.db.scalars(stmt))

    def list_distinct_categories(self) -> list[str]:
        stmt = select(Course.category).where(Course.category.is_not(None)).distinct().order_by(Course.category.asc())
        return [value for value in self.db.scalars(stmt) if value]

    def delete(self, course: Course) -> None:
        self.db.delete(course)
