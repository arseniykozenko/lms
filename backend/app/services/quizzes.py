from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.models.quiz import Question, Quiz, QuizAnswer, QuizAttempt
from app.models.user import UserRole
from app.repositories.module import ModuleRepository
from app.repositories.quiz import QuizRepository
from app.schemas.quiz import (
    QuestionRead,
    QuizAttemptRead,
    QuizCreate,
    QuizRead,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizUpdate,
)
from app.schemas.user import UserRead
from app.services.courses import CourseService, get_course_service
from app.services.notifications import NotificationService, get_notification_service


class QuizService:
    def __init__(self, db: Session, courses: CourseService, notifications: NotificationService) -> None:
        self.db = db
        self.quizzes = QuizRepository(db)
        self.modules = ModuleRepository(db)
        self.courses = courses
        self.notifications = notifications

    def create_quiz(self, module_id: UUID, payload: QuizCreate, current_user: UserRead) -> QuizRead:
        module = self._get_module_or_404(module_id)
        self.courses.ensure_can_manage_course(module.course_id, current_user)
        if self.quizzes.get_by_module_id(module_id) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Quiz already exists for this module")
        quiz = Quiz(
            module_id=module_id,
            title=payload.title,
            due_at=self._normalize_datetime(payload.due_at),
            is_published=payload.is_published,
        )
        self.quizzes.create(quiz)
        for index, question_payload in enumerate(payload.questions, start=1):
            if question_payload.correct_option not in question_payload.options:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="correct_option must be one of the provided options",
                )
            self.quizzes.create_question(
                Question(
                    quiz_id=quiz.id,
                    content=question_payload.content,
                    options_json=question_payload.options,
                    correct_option=question_payload.correct_option,
                    explanation=question_payload.explanation,
                    position=question_payload.position or index,
                )
            )
        self.db.commit()
        stored = self.quizzes.get_by_module_id(module_id)
        assert stored is not None
        if stored.is_published:
            self.notifications.create_quiz_published_notifications(
                module.course_id,
                module_id=module.id,
                quiz_id=stored.id,
                quiz_title=stored.title,
            )
        return self._to_quiz_read(stored, include_correct_option=True)

    def get_module_quiz(self, module_id: UUID, current_user: UserRead) -> QuizRead:
        module = self._get_module_or_404(module_id)
        if not self.courses.has_course_access(module.course_id, current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not enrolled in this course")
        quiz = self.quizzes.get_by_module_id(module_id)
        if quiz is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
        if (
            not quiz.is_published
            and current_user.role != UserRole.ADMIN
            and quiz.module.course.author_id != current_user.id
            and not self.courses.is_course_collaborator(quiz.module.course_id, current_user.id)
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Quiz is not published")
        can_manage = current_user.role == UserRole.ADMIN or quiz.module.course.author_id == current_user.id
        if current_user.role == UserRole.TEACHER and self.courses.is_course_collaborator(quiz.module.course_id, current_user.id):
            can_manage = True
        return self._to_quiz_read(quiz, include_correct_option=can_manage)

    def get_quiz(self, quiz_id: UUID, current_user: UserRead) -> QuizRead:
        quiz = self._get_quiz_or_404(quiz_id)
        if not self.courses.has_course_access(quiz.module.course_id, current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not enrolled in this course")
        if (
            not quiz.is_published
            and current_user.role != UserRole.ADMIN
            and quiz.module.course.author_id != current_user.id
            and not self.courses.is_course_collaborator(quiz.module.course_id, current_user.id)
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Quiz is not published")
        can_manage = current_user.role == UserRole.ADMIN or quiz.module.course.author_id == current_user.id
        if current_user.role == UserRole.TEACHER and self.courses.is_course_collaborator(quiz.module.course_id, current_user.id):
            can_manage = True
        return self._to_quiz_read(quiz, include_correct_option=can_manage)

    def update_quiz(self, quiz_id: UUID, payload: QuizUpdate, current_user: UserRead) -> QuizRead:
        quiz = self._get_quiz_or_404(quiz_id)
        self.courses.ensure_can_manage_course(quiz.module.course_id, current_user)
        previous_due_at = quiz.due_at
        was_published = quiz.is_published
        questions_changed = self._questions_changed(quiz, payload)
        quiz.title = payload.title
        quiz.due_at = self._normalize_datetime(payload.due_at)
        quiz.is_published = payload.is_published
        if questions_changed:
            self._ensure_quiz_questions_mutable(quiz)
            quiz.questions.clear()
            self.db.flush()
            for index, question_payload in enumerate(payload.questions, start=1):
                if question_payload.correct_option not in question_payload.options:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="correct_option must be one of the provided options",
                    )
                quiz.questions.append(
                    Question(
                        quiz_id=quiz.id,
                        content=question_payload.content,
                        options_json=question_payload.options,
                        correct_option=question_payload.correct_option,
                        explanation=question_payload.explanation,
                        position=question_payload.position or index,
                    )
                )
        self.db.commit()
        self.db.refresh(quiz)
        if quiz.is_published and not was_published:
            self.notifications.create_quiz_published_notifications(
                quiz.module.course_id,
                module_id=quiz.module_id,
                quiz_id=quiz.id,
                quiz_title=quiz.title,
            )
        if quiz.is_published and previous_due_at != quiz.due_at:
            self.notifications.create_deadline_changed_notifications(
                quiz.module.course_id,
                module_id=quiz.module_id,
                entity_kind="теста",
                entity_id=quiz.id,
                item_title=quiz.title,
                previous_due_at=previous_due_at,
                due_at=quiz.due_at,
            )
        return self._to_quiz_read(quiz, include_correct_option=True)

    def delete_quiz(self, quiz_id: UUID, current_user: UserRead) -> None:
        quiz = self._get_quiz_or_404(quiz_id)
        self.courses.ensure_can_manage_course(quiz.module.course_id, current_user)
        self.courses.ensure_can_delete_course_resources(quiz.module.course_id, current_user)
        self._ensure_quiz_questions_mutable(quiz)
        self.db.delete(quiz)
        self.db.commit()

    def submit_quiz(self, quiz_id: UUID, payload: QuizSubmitRequest, current_user: UserRead) -> QuizSubmitResponse:
        quiz = self._get_quiz_or_404(quiz_id)
        if not self.courses.has_course_access(quiz.module.course_id, current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not enrolled in this course")
        ordered_questions = sorted(quiz.questions, key=lambda item: (item.position, str(item.id)))
        answers_by_question = {answer.question_id: answer.selected_option for answer in payload.answers}
        expected_question_ids = {question.id for question in ordered_questions}
        provided_question_ids = set(answers_by_question.keys())

        if len(payload.answers) != len(provided_question_ids):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Duplicate answers are not allowed")

        if provided_question_ids != expected_question_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="You must answer every question in the quiz",
            )

        results = []
        score = 0
        attempt = QuizAttempt(quiz_id=quiz.id, user_id=current_user.id, score=0, total_questions=len(ordered_questions))
        self.quizzes.create_attempt(attempt)
        for question in ordered_questions:
            selected = answers_by_question.get(question.id)
            if selected not in question.options_json:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Selected option must be one of the provided options",
                )
            is_correct = selected == question.correct_option
            if is_correct:
                score += 1
            self.db.add(
                QuizAnswer(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    selected_option=selected,
                    is_correct=is_correct,
                )
            )
            results.append(
                {
                    "question_id": question.id,
                    "selected_option": selected,
                    "is_correct": is_correct,
                    "explanation": question.explanation,
                }
            )
        attempt.score = score
        self.db.commit()
        self.db.refresh(attempt)
        self._trim_attempts_history(quiz.id, current_user.id)
        self.db.commit()
        return QuizSubmitResponse(
            id=attempt.id,
            quiz_id=attempt.quiz_id,
            user_id=attempt.user_id,
            score=attempt.score,
            total_questions=attempt.total_questions,
            is_late=bool(quiz.due_at is not None and attempt.created_at > quiz.due_at),
            created_at=attempt.created_at,
            results=results,
        )

    def list_my_attempts(self, quiz_id: UUID, current_user: UserRead) -> list[QuizAttemptRead]:
        quiz = self._get_quiz_or_404(quiz_id)
        if not self.courses.has_course_access(quiz.module.course_id, current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not enrolled in this course")
        attempts = self.quizzes.list_attempts_for_user(quiz_id, current_user.id)
        return [self._to_attempt_read(attempt) for attempt in attempts[:3]]

    def _get_module_or_404(self, module_id: UUID):
        module = self.modules.get_by_id(module_id)
        if module is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
        return module

    def _get_quiz_or_404(self, quiz_id: UUID) -> Quiz:
        quiz = self.quizzes.get_by_id(quiz_id)
        if quiz is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
        return quiz

    def _ensure_quiz_questions_mutable(self, quiz: Quiz) -> None:
        if quiz.attempts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Quiz questions cannot be changed or deleted after saved attempts",
            )

    def _questions_changed(self, quiz: Quiz, payload: QuizUpdate) -> bool:
        current_questions = [
            (
                question.content,
                list(question.options_json),
                question.correct_option,
                question.explanation,
                question.position,
            )
            for question in sorted(quiz.questions, key=lambda item: (item.position, str(item.id)))
        ]
        incoming_questions = [
            (
                question.content,
                list(question.options),
                question.correct_option,
                question.explanation,
                question.position,
            )
            for question in payload.questions
        ]
        return current_questions != incoming_questions

    def _to_quiz_read(self, quiz: Quiz, *, include_correct_option: bool = False) -> QuizRead:
        ordered_questions = sorted(quiz.questions, key=lambda item: (item.position, str(item.id)))
        return QuizRead(
            id=quiz.id,
            module_id=quiz.module_id,
            title=quiz.title,
            due_at=quiz.due_at,
            is_published=quiz.is_published,
            has_attempts=bool(quiz.attempts),
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
            questions=[
                QuestionRead(
                    id=question.id,
                    content=question.content,
                    options=question.options_json,
                    correct_option=question.correct_option if include_correct_option else None,
                    explanation=question.explanation,
                    position=question.position,
                )
                for question in ordered_questions
            ],
        )

    def _to_attempt_read(self, attempt: QuizAttempt) -> QuizAttemptRead:
        ordered_answers = sorted(
            attempt.answers,
            key=lambda item: (item.question.position if item.question else 0, str(item.question_id)),
        )
        return QuizAttemptRead(
            id=attempt.id,
            quiz_id=attempt.quiz_id,
            user_id=attempt.user_id,
            score=attempt.score,
            total_questions=attempt.total_questions,
            is_late=bool(attempt.quiz.due_at is not None and attempt.created_at > attempt.quiz.due_at),
            created_at=attempt.created_at,
            results=[
                {
                    "question_id": answer.question_id,
                    "selected_option": answer.selected_option,
                    "is_correct": answer.is_correct,
                    "explanation": answer.question.explanation if answer.question else None,
                }
                for answer in ordered_answers
            ],
        )

    def _trim_attempts_history(self, quiz_id: UUID, user_id: UUID) -> None:
        attempts = self.quizzes.list_attempts_for_user(quiz_id, user_id)
        for attempt in attempts[3:]:
            self.db.delete(attempt)

    def _normalize_datetime(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


def get_quiz_service(
    db: Session = Depends(get_db),
    courses: CourseService = Depends(get_course_service),
    notifications: NotificationService = Depends(get_notification_service),
) -> QuizService:
    return QuizService(db, courses, notifications)
