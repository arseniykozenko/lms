from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.module_content import ModuleContentType


class ModuleContentTextCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    text_content: str = Field(min_length=1)


class ModuleContentLinkCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    source_url: str = Field(min_length=1, max_length=500)


class ModuleContentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    text_content: str | None = None
    source_url: str | None = Field(default=None, max_length=500)


class ModuleContentReorderItem(BaseModel):
    id: UUID


class ModuleContentReorderRequest(BaseModel):
    contents: list[ModuleContentReorderItem] = Field(min_length=1)


class ModuleContentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module_id: UUID
    title: str
    content_type: ModuleContentType
    position: int
    text_content: str | None
    asset_url: str | None
    source_url: str | None
    transcript_text: str | None = None
    transcript_summary: str | None = None
    transcript_timestamps_json: list[dict] | None = None
    transcript_status: str | None = None
    transcript_error: str | None = None
    transcript_updated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
