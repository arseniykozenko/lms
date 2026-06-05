from __future__ import annotations

from datetime import UTC, datetime, timedelta
from math import ceil, floor
from uuid import UUID

from sqlalchemy import delete, select

from app.core.db.session import SessionLocal
from app.core.security.password import hash_password
from app.models.assignment import AssignmentSubmission, SubmissionStatus
from app.models.content_progress import ContentProgress
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.quiz import QuizAttempt
from app.models.user import User, UserRole
from app.schemas.user import UserRead
from app.services.progress import ProgressService


COURSE_TITLE = "Основы Golang"
TARGET_STUDENTS = [
    ("lowrisk.golang1@lms.dev", "Роман", "Низкорисков"),
    ("lowrisk.golang2@lms.dev", "Мария", "Низкорискова"),
]


def create_or_get_student(db, email: str, first_name: str, second_name: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is not None:
        return user
    user = User(
        email=email,
        password_hash=hash_password("demo12345"),
        role=UserRole.STUDENT,
        first_name=first_name,
        second_name=second_name,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def ensure_enrollment(db, user_id: UUID, course_id: UUID, enrolled_at: datetime) -> None:
    enrollment = db.scalar(select(Enrollment).where(Enrollment.user_id == user_id, Enrollment.course_id == course_id))
    if enrollment is None:
        db.add(Enrollment(user_id=user_id, course_id=course_id, enrolled_at=enrolled_at))
    else:
        enrollment.enrolled_at = enrolled_at
    db.flush()


def reset_course_activity(db, user_id: UUID, content_ids: list[UUID], assignment_ids: list[UUID], quiz_ids: list[UUID]) -> None:
    if content_ids:
        db.execute(delete(ContentProgress).where(ContentProgress.user_id == user_id, ContentProgress.content_id.in_(content_ids)))
    if assignment_ids:
        db.execute(
            delete(AssignmentSubmission).where(
                AssignmentSubmission.student_id == user_id,
                AssignmentSubmission.assignment_id.in_(assignment_ids),
            )
        )
    if quiz_ids:
        db.execute(delete(QuizAttempt).where(QuizAttempt.user_id == user_id, QuizAttempt.quiz_id.in_(quiz_ids)))


def main() -> None:
    now = datetime.now(UTC)
    # Keep last activity in 3..6 days window -> +5 inactivity risk.
    activity_at = now - timedelta(days=4, hours=2)
    enrolled_at = now - timedelta(days=21)

    with SessionLocal() as db:
        course = db.scalar(select(Course).where(Course.title == COURSE_TITLE))
        if course is None:
            raise SystemExit(f"Course not found: {COURSE_TITLE}")

        modules = [m for m in course.modules if m.is_published]
        contents = [c for m in modules for c in m.contents]
        assignments = [a for m in modules for a in m.assignments if a.is_published]
        quizzes = [m.quiz for m in modules if m.quiz is not None and m.quiz.is_published]

        content_ids = [c.id for c in contents]
        assignment_ids = [a.id for a in assignments]
        quiz_ids = [q.id for q in quizzes]

        for student_idx, (email, first_name, second_name) in enumerate(TARGET_STUDENTS):
            user = create_or_get_student(db, email, first_name, second_name)
            ensure_enrollment(db, user.id, course.id, enrolled_at)
            reset_course_activity(db, user.id, content_ids, assignment_ids, quiz_ids)

            # View all content (high engagement, no pseudo activity).
            for content in contents:
                db.add(
                    ContentProgress(
                        user_id=user.id,
                        content_id=content.id,
                        viewed_at=activity_at,
                        updated_at=activity_at,
                    )
                )

            # Grade all assignments (no pending/overdue/late penalties).
            for assignment in assignments:
                max_score = assignment.max_score or 100
                score = max(1, int(max_score * 0.9))
                db.add(
                    AssignmentSubmission(
                        assignment_id=assignment.id,
                        student_id=user.id,
                        attempt_number=1,
                        answer_markdown="Решение выполнено и отправлено.",
                        status=SubmissionStatus.GRADED,
                        score=score,
                        submitted_at=activity_at,
                        graded_at=activity_at + timedelta(hours=2),
                        updated_at=activity_at + timedelta(hours=2),
                    )
                )

            # One failed quiz + others passed -> risk about 17 (12 + 5 inactivity).
            failed_quiz_index = student_idx % max(1, len(quizzes))
            for quiz_idx, quiz in enumerate(quizzes):
                total = max(1, len(quiz.questions))
                if quiz_idx == failed_quiz_index:
                    score = max(0, floor(total * 0.4))
                else:
                    score = max(1, ceil(total * 0.8))
                db.add(
                    QuizAttempt(
                        quiz_id=quiz.id,
                        user_id=user.id,
                        score=score,
                        total_questions=total,
                        created_at=activity_at + timedelta(hours=3),
                    )
                )

        db.commit()

        progress_service = ProgressService(db)
        print(f"Added/updated {len(TARGET_STUDENTS)} low-risk demo students for course '{course.title}'.")
        for email, *_ in TARGET_STUDENTS:
            user = db.scalar(select(User).where(User.email == email))
            assert user is not None
            analytics = progress_service.build_student_course_analytics(course.id, UserRead.model_validate(user))
            progress = analytics["progress"]
            print(
                f"{email} | progress={progress.progress_percent}% | "
                f"risk={analytics['risk_level']}:{analytics['risk_score']} | inactivity={analytics['inactivity_days']}"
            )


if __name__ == "__main__":
    main()
