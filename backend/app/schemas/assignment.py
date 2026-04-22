from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.assignment import SubmissionStatus
from app.schemas.user import UserRead


class AssignmentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    instructions_markdown: str = Field(min_length=1)
    max_score: int | None = Field(default=None, ge=0, le=100)
    is_published: bool = True


class AssignmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    instructions_markdown: str | None = Field(default=None, min_length=1)
    max_score: int | None = Field(default=None, ge=0, le=100)
    is_published: bool | None = None


class AssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module_id: UUID
    title: str
    instructions_markdown: str
    attachment_url: str | None = None
    attachment_name: str | None = None
    max_score: int | None = None
    is_published: bool
    has_submissions: bool = False
    attachments: list["AssignmentAttachmentRead"] = []
    created_at: datetime
    updated_at: datetime


class AssignmentAttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_url: str
    file_name: str
    created_at: datetime


class AssignmentSubmissionCreate(BaseModel):
    answer_markdown: str | None = None


class AssignmentSubmissionGrade(BaseModel):
    score: int | None = Field(default=None, ge=0, le=100)
    feedback_markdown: str | None = None


class AssignmentSubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assignment_id: UUID
    student_id: UUID
    attempt_number: int
    answer_markdown: str | None = None
    attachment_url: str | None = None
    attachment_name: str | None = None
    status: SubmissionStatus
    score: int | None = None
    feedback_markdown: str | None = None
    submitted_at: datetime
    graded_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    student: UserRead | None = None
    attachments: list[AssignmentAttachmentRead] = []


AssignmentRead.model_rebuild()
