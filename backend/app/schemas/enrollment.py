from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enrollment import EnrollmentStatus


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
    full_name: str | None = None
    email: str
    profile_photo_url: str | None = None


class CourseStudentEnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    status: EnrollmentStatus
    enrolled_at: datetime
    user: EnrolledStudentRead
