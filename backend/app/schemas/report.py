from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.report import ReportStatus, ReportTargetType
from app.schemas.user import UserRead


class ReportCreate(BaseModel):
    target_type: ReportTargetType
    course_id: UUID | None = None
    comment_id: UUID | None = None
    chat_message_id: UUID | None = None
    module_content_id: UUID | None = None
    category: str = Field(min_length=2, max_length=64)
    reason: str = Field(min_length=3, max_length=120)
    details: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_target(self) -> "ReportCreate":
        if self.target_type == ReportTargetType.COURSE and self.course_id is None:
            raise ValueError("course_id is required for course reports")
        if self.target_type == ReportTargetType.COMMENT and self.comment_id is None:
            raise ValueError("comment_id is required for comment reports")
        if self.target_type == ReportTargetType.CHAT_MESSAGE and self.chat_message_id is None:
            raise ValueError("chat_message_id is required for chat message reports")
        if self.target_type == ReportTargetType.MODULE_CONTENT and self.module_content_id is None:
            raise ValueError("module_content_id is required for module content reports")
        return self


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    target_type: ReportTargetType
    course_id: UUID | None = None
    comment_id: UUID | None = None
    chat_message_id: UUID | None = None
    module_content_id: UUID | None = None
    category: str
    reason: str
    details: str | None = None
    status: ReportStatus
    resolution_note: str | None = None
    created_at: datetime
    reviewed_at: datetime | None = None
    link_url: str | None = None
    reporter: UserRead
    reviewer: UserRead | None = None


class ReportReviewUpdate(BaseModel):
    status: ReportStatus
    resolution_note: str | None = Field(default=None, max_length=2000)
