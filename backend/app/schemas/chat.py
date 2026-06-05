from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    recipient_id: UUID
    content: str


class ChatMessageRead(BaseModel):
    id: UUID
    sender_id: UUID
    recipient_id: UUID
    sender_name: str
    sender_profile_photo_url: str | None = None
    recipient_name: str
    recipient_profile_photo_url: str | None = None
    content: str
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime
    course_id: UUID | None = None
    course_title: str | None = None


class ChatConversationRead(BaseModel):
    partner_id: UUID
    partner_name: str
    partner_profile_photo_url: str | None = None
    partner_email: str
    partner_role: str
    course_id: UUID | None = None
    course_title: str | None = None
    unread_count: int = 0
    last_message: str | None = None
    last_message_at: datetime | None = None


class ChatGroupCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    member_ids: list[UUID] = Field(default_factory=list)


class ChatGroupRead(BaseModel):
    id: UUID
    title: str
    created_by_user_id: UUID
    members: list[UUID]
    created_at: datetime
    updated_at: datetime


class ChatGroupMessageCreate(BaseModel):
    content: str


class ChatGroupMessageRead(BaseModel):
    id: UUID
    group_id: UUID
    sender_id: UUID
    sender_name: str
    sender_profile_photo_url: str | None = None
    content: str
    created_at: datetime
