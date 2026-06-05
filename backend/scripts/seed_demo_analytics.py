from __future__ import annotations

import argparse
import random
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select

from app.core.db.session import SessionLocal
from app.core.security.password import hash_password
from app.models.assignment import AssignmentSubmission, SubmissionStatus
from app.models.content_progress import ContentProgress
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.module_content import ModuleContent
from app.models.quiz import Quiz, QuizAttempt
from app.models.user import User, UserRole


SCENARIOS = ["low", "medium", "high", "pseudo", "newbie"]


def pick_scenario(index: int) -> str:
    return SCENARIOS[index % len(SCENARIOS)]


def random_past(days_from: int, days_to: int) -> datetime:
    now = datetime.now(UTC)
    delta_days = random.randint(days_from, days_to)
    delta_hours = random.randint(0, 23)
    return now - timedelta(days=delta_days, hours=delta_hours)


def create_or_get_demo_student(db, email: str, first_name: str, second_name: str) -> User:
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


def ensure_enrollment(db, user_id: UUID, course_id: UUID, scenario: str) -> Enrollment:
    enrollment = db.scalar(select(Enrollment).where(Enrollment.user_id == user_id, Enrollment.course_id == course_id))
    if enrollment is None:
        enrolled_at = random_past(1, 3) if scenario == "newbie" else random_past(10, 40)
        enrollment = Enrollment(user_id=user_id, course_id=course_id, enrolled_at=enrolled_at)
        db.add(enrollment)
        db.flush()
    return enrollment


def reset_student_course_activity(db, user_id: UUID, content_ids: list[UUID], assignment_ids: list[UUID], quiz_ids: list[UUID]) -> None:
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


def seed_content_views(db, user_id: UUID, contents: list[ModuleContent], scenario: str) -> None:
    if not contents:
        return
    if scenario == "low":
        ratio = 0.85
    elif scenario == "medium":
        ratio = 0.55
    elif scenario == "high":
        ratio = 0.2
    elif scenario == "pseudo":
        ratio = 0.75
    else:  # newbie
        ratio = 0.35

    views_count = max(1, int(len(contents) * ratio))
    selected = random.sample(contents, min(views_count, len(contents)))
    for content in selected:
        viewed_at = random_past(0, 6) if scenario in {"pseudo", "newbie"} else random_past(1, 20)
        db.add(
            ContentProgress(
                user_id=user_id,
                content_id=content.id,
                viewed_at=viewed_at,
                updated_at=viewed_at,
            )
        )


def seed_assignments(db, user_id: UUID, assignments: list, scenario: str) -> None:
    if not assignments:
        return

    if scenario == "low":
        graded_ratio = 0.8
        pending_ratio = 0.1
    elif scenario == "medium":
        graded_ratio = 0.45
        pending_ratio = 0.25
    elif scenario == "high":
        graded_ratio = 0.1
        pending_ratio = 0.15
    elif scenario == "pseudo":
        graded_ratio = 0.0
        pending_ratio = 0.0
    else:  # newbie
        graded_ratio = 0.15
        pending_ratio = 0.1

    graded_count = int(len(assignments) * graded_ratio)
    pending_count = int(len(assignments) * pending_ratio)
    shuffled = assignments[:]
    random.shuffle(shuffled)
    graded_items = shuffled[:graded_count]
    pending_items = shuffled[graded_count : graded_count + pending_count]

    for assignment in graded_items:
        submitted_at = random_past(2, 18)
        graded_at = submitted_at + timedelta(hours=random.randint(5, 48))
        max_score = assignment.max_score or 100
        score_ratio = random.uniform(0.75, 0.98) if scenario == "low" else random.uniform(0.55, 0.82)
        score = max(1, int(max_score * score_ratio))
        db.add(
            AssignmentSubmission(
                assignment_id=assignment.id,
                student_id=user_id,
                attempt_number=1,
                answer_markdown="Демо-ответ",
                status=SubmissionStatus.GRADED,
                score=score,
                submitted_at=submitted_at,
                graded_at=graded_at,
                updated_at=graded_at,
            )
        )

    for assignment in pending_items:
        submitted_at = random_past(0, 7)
        db.add(
            AssignmentSubmission(
                assignment_id=assignment.id,
                student_id=user_id,
                attempt_number=1,
                answer_markdown="Ответ ожидает проверки",
                status=SubmissionStatus.SUBMITTED,
                submitted_at=submitted_at,
                updated_at=submitted_at,
            )
        )


def seed_quizzes(db, user_id: UUID, quizzes: list[Quiz], scenario: str) -> None:
    if not quizzes:
        return

    for quiz in quizzes:
        total = max(1, len(quiz.questions))
        if scenario == "low":
            score = max(1, int(total * random.uniform(0.7, 1.0)))
            attempts_count = 1
        elif scenario == "medium":
            score = max(0, int(total * random.uniform(0.4, 0.75)))
            attempts_count = random.choice([1, 2])
        elif scenario == "high":
            score = max(0, int(total * random.uniform(0.0, 0.45)))
            attempts_count = 1
        elif scenario == "pseudo":
            continue
        else:  # newbie
            if random.random() < 0.6:
                continue
            score = max(0, int(total * random.uniform(0.3, 0.7)))
            attempts_count = 1

        for idx in range(attempts_count):
            attempt_score = score if idx == attempts_count - 1 else max(0, score - 1)
            created_at = random_past(0, 10) if scenario in {"medium", "newbie"} else random_past(2, 18)
            db.add(
                QuizAttempt(
                    quiz_id=quiz.id,
                    user_id=user_id,
                    score=attempt_score,
                    total_questions=total,
                    created_at=created_at,
                )
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo analytics activity for a course")
    parser.add_argument("--course-id", required=True, help="Course UUID")
    parser.add_argument("--students", type=int, default=25, help="How many demo students to create")
    parser.add_argument("--email-prefix", default="demo.student", help="Email prefix")
    parser.add_argument("--domain", default="example.com", help="Email domain")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    random.seed(args.seed)
    course_id = UUID(args.course_id)

    with SessionLocal() as db:
        course = db.get(Course, course_id)
        if course is None:
            raise SystemExit("Course not found")

        modules = [m for m in course.modules if m.is_published]
        contents = [c for m in modules for c in m.contents]
        assignments = [a for m in modules for a in m.assignments if a.is_published]
        quizzes = [m.quiz for m in modules if m.quiz is not None and m.quiz.is_published]

        content_ids = [c.id for c in contents]
        assignment_ids = [a.id for a in assignments]
        quiz_ids = [q.id for q in quizzes]

        created = 0
        for index in range(args.students):
            scenario = pick_scenario(index)
            email = f"{args.email_prefix}{index + 1}@{args.domain}".lower()
            user = create_or_get_demo_student(db, email, f"Демо{index + 1}", "Студент")
            ensure_enrollment(db, user.id, course_id, scenario)
            reset_student_course_activity(db, user.id, content_ids, assignment_ids, quiz_ids)
            seed_content_views(db, user.id, contents, scenario)
            seed_assignments(db, user.id, assignments, scenario)
            seed_quizzes(db, user.id, quizzes, scenario)
            created += 1

        db.commit()
        print(
            f"Done. Seeded {created} demo students for course {course.title} ({course.id}). "
            "Scenarios: low/medium/high/pseudo/newbie."
        )


if __name__ == "__main__":
    main()
