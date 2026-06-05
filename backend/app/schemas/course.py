from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.course_collaborator import CourseCollaboratorStatus
from app.schemas.progress import CourseProgressSummary


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=120)
    description: str = Field(min_length=1)
    thumbnail_url: str | None = Field(default=None, max_length=500)
    is_free: bool = True
    is_published: bool = False


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, min_length=1)
    thumbnail_url: str | None = Field(default=None, max_length=500)
    is_free: bool | None = None
    is_published: bool | None = None


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author_id: UUID
    title: str
    category: str | None = None
    description: str
    thumbnail_url: str | None
    is_free: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime


class EnrolledCourseRead(CourseRead):
    enrolled_at: datetime
    progress: CourseProgressSummary | None = None
    progress_status: str = "not_started"
    last_activity_at: datetime | None = None
    inactivity_days: int | None = None
    pending_assignments_count: int = 0
    overdue_items_count: int = 0
    upcoming_deadlines_count: int = 0
    average_assignment_score_percent: int | None = None
    average_quiz_score_percent: int | None = None
    recent_completed_items_7d: int = 0
    engagement_trend: str = "stable"


class CourseCollaboratorInviteCreate(BaseModel):
    teacher_email: str = Field(min_length=3, max_length=255)
    message: str | None = Field(default=None, max_length=500)


class CourseCollaboratorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    course_title: str | None = None
    user_id: UUID
    invited_by_user_id: UUID
    status: CourseCollaboratorStatus
    invite_message: str | None = None
    created_at: datetime
    updated_at: datetime
    accepted_at: datetime | None = None
    user_name: str | None = None
    user_email: str | None = None
    inviter_name: str | None = None
    inviter_email: str | None = None
