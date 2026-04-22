from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    thumbnail_url: str | None = Field(default=None, max_length=500)
    is_free: bool = True
    is_published: bool = False


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    thumbnail_url: str | None = Field(default=None, max_length=500)
    is_free: bool | None = None
    is_published: bool | None = None


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author_id: UUID
    title: str
    description: str
    thumbnail_url: str | None
    is_free: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime


class EnrolledCourseRead(CourseRead):
    enrolled_at: datetime
