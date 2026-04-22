from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ModuleCreate(BaseModel):
    course_id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    video_url: str | None = Field(default=None, max_length=500)
    is_published: bool = False


class ModuleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    video_url: str | None = Field(default=None, max_length=500)
    is_published: bool | None = None


class ModuleReorderItem(BaseModel):
    id: UUID


class ModuleReorderRequest(BaseModel):
    modules: list[ModuleReorderItem] = Field(min_length=1)


class ModuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    course_title: str | None = None
    title: str
    description: str | None
    video_url: str | None
    position: int
    is_published: bool
    created_at: datetime
    updated_at: datetime
