from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.quiz import Question, Quiz, QuizAnswer, QuizAttempt


class QuizRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, quiz: Quiz) -> Quiz:
        self.db.add(quiz)
        self.db.flush()
        return quiz

    def get_by_id(self, quiz_id: UUID) -> Quiz | None:
        stmt = (
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.id == quiz_id)
        )
        return self.db.scalar(stmt)

    def get_by_module_id(self, module_id: UUID) -> Quiz | None:
        stmt = (
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.module_id == module_id)
        )
        return self.db.scalar(stmt)

    def create_question(self, question: Question) -> Question:
        self.db.add(question)
        self.db.flush()
        return question

    def create_attempt(self, attempt: QuizAttempt) -> QuizAttempt:
        self.db.add(attempt)
        self.db.flush()
        return attempt

    def list_attempts_for_user(self, quiz_id: UUID, user_id: UUID) -> list[QuizAttempt]:
        stmt = (
            select(QuizAttempt)
            .options(selectinload(QuizAttempt.quiz), selectinload(QuizAttempt.answers).selectinload(QuizAnswer.question))
            .where(QuizAttempt.quiz_id == quiz_id, QuizAttempt.user_id == user_id)
            .order_by(QuizAttempt.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def has_attempt_for_user(self, quiz_id: UUID, user_id: UUID) -> bool:
        stmt = select(QuizAttempt.id).where(QuizAttempt.quiz_id == quiz_id, QuizAttempt.user_id == user_id).limit(1)
        return self.db.scalar(stmt) is not None

    def has_passing_attempt_for_user(self, quiz_id: UUID, user_id: UUID, passing_ratio: float) -> bool:
        attempts = self.list_attempts_for_user(quiz_id, user_id)
        for attempt in attempts:
            if attempt.total_questions <= 0:
                continue
            if (attempt.score / attempt.total_questions) >= passing_ratio:
                return True
        return False
