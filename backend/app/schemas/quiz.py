from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuestionCreate(BaseModel):
    content: str = Field(min_length=1)
    options: list[str] = Field(min_length=2, max_length=6)
    correct_option: str = Field(min_length=1)
    explanation: str | None = None
    position: int = Field(default=1, ge=1)

    @field_validator("correct_option")
    @classmethod
    def validate_correct_option(cls, value: str) -> str:
        return value.strip()


class QuizCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    due_at: datetime | None = None
    is_published: bool = False
    questions: list[QuestionCreate] = Field(min_length=1)


class QuizUpdate(QuizCreate):
    pass


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content: str
    options: list[str]
    correct_option: str | None = None
    explanation: str | None
    position: int


class QuizRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module_id: UUID
    title: str
    due_at: datetime | None = None
    is_published: bool
    has_attempts: bool = False
    created_at: datetime
    updated_at: datetime
    questions: list[QuestionRead]


class QuizQuestionResult(BaseModel):
    question_id: UUID
    selected_option: str
    is_correct: bool
    explanation: str | None = None


class QuizSubmitAnswer(BaseModel):
    question_id: UUID
    selected_option: str = Field(min_length=1)


class QuizSubmitRequest(BaseModel):
    answers: list[QuizSubmitAnswer] = Field(min_length=1)


class QuizAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    quiz_id: UUID
    user_id: UUID
    score: int
    total_questions: int
    is_late: bool = False
    created_at: datetime
    results: list[QuizQuestionResult] = Field(default_factory=list)


class QuizSubmitResponse(QuizAttemptRead):
    results: list[QuizQuestionResult]
