from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enrollment import EnrollmentStatus
from app.schemas.progress import CourseProgressSummary


class EnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    course_id: UUID
    status: EnrollmentStatus
    enrolled_at: datetime


class EnrolledStudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str | None = None
    second_name: str | None = None
    email: str
    profile_photo_url: str | None = None


class CourseStudentEnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    status: EnrollmentStatus
    enrolled_at: datetime
    user: EnrolledStudentRead
    progress: CourseProgressSummary | None = None
    progress_status: str = "not_started"
    last_activity_at: datetime | None = None
    inactivity_days: int | None = None
    pending_assignments_count: int = 0
    passed_quizzes_count: int = 0
    failed_quizzes_count: int = 0
    overdue_items_count: int = 0
    upcoming_deadlines_count: int = 0
    late_submissions_count: int = 0
    average_assignment_score_percent: int | None = None
    average_quiz_score_percent: int | None = None
    recent_activity_count_7d: int = 0
    recent_completed_items_7d: int = 0
    pseudo_activity: bool = False
    engagement_trend: str = "stable"
    risk_score: int = 0
    risk_level: str = "low"
