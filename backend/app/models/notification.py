from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.session import Base


class NotificationType(StrEnum):
    COMMENT_REPLY = "comment_reply"
    ASSIGNMENT_GRADED = "assignment_graded"
    ASSIGNMENT_FEEDBACK = "assignment_feedback"
    ASSIGNMENT_SUBMITTED = "assignment_submitted"
    ASSIGNMENT_PUBLISHED = "assignment_published"
    QUIZ_PUBLISHED = "quiz_published"
    DEADLINE_CHANGED = "deadline_changed"
    TEACHER_ANNOUNCEMENT = "teacher_announcement"
    CHAT_MESSAGE = "chat_message"
    PERFORMANCE_RISK = "performance_risk"
    DEADLINE_SOON = "deadline_soon"
    DEADLINE_OVERDUE = "deadline_overdue"


notification_type_enum = Enum(
    NotificationType,
    name="notification_type",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("dedupe_key", name="uq_notifications_dedupe_key"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[NotificationType] = mapped_column(notification_type_enum, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    link_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    user: Mapped["User"] = relationship(back_populates="notifications")
