from __future__ import annotations

from sqlalchemy import or_, select

from app.core.db.session import SessionLocal
from app.models.course import Course
from app.models.user import User, UserRole


PLACEHOLDER_COURSES = [
    {
        "title": "Продвинутый Golang: микросервисы",
        "description": (
            "Практический курс по проектированию и разработке микросервисов на Go: "
            "архитектура сервисов, конфигурация, observability, очереди и CI/CD."
        ),
        "category": "Backend",
        "thumbnail_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "title": "Алгоритмы и структуры данных для разработчика",
        "description": (
            "Курс по базовым и продвинутым структурам данных, анализу сложности алгоритмов "
            "и разбору практических задач для инженерной подготовки."
        ),
        "category": "Computer Science",
        "thumbnail_url": "https://images.unsplash.com/photo-1509228627152-72ae9ae6848d?auto=format&fit=crop&w=1200&q=80",
    },
]


def main() -> None:
    with SessionLocal() as db:
        author = db.scalar(
            select(User)
            .where(
                User.is_active.is_(True),
                or_(User.role == UserRole.TEACHER, User.role == UserRole.ADMIN),
            )
            .order_by(User.created_at.asc())
        )
        if author is None:
            raise SystemExit("No active teacher/admin found to assign as course author.")

        existing_titles = set(db.scalars(select(Course.title)).all())
        created = 0

        for spec in PLACEHOLDER_COURSES:
            if spec["title"] in existing_titles:
                print(f"Skip existing course: {spec['title']}")
                continue

            course = Course(
                author_id=author.id,
                title=spec["title"],
                description=spec["description"],
                category=spec["category"],
                thumbnail_url=spec["thumbnail_url"],
                is_free=True,
                is_published=True,
            )
            db.add(course)
            created += 1
            print(f"Created course: {course.title}")

        db.commit()
        print(f"Done. Added {created} placeholder courses.")


if __name__ == "__main__":
    main()
