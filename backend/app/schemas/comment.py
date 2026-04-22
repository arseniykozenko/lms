from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserRead


class CommentCreate(BaseModel):
    content: str = Field(min_length=1)
    parent_comment_id: UUID | None = None


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module_id: UUID
    parent_comment_id: UUID | None = None
    content: str
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    user: UserRead
    replies: list["CommentRead"] = Field(default_factory=list)


class CommentDeleteResponse(BaseModel):
    id: UUID
    module_id: UUID


CommentRead.model_rebuild()
