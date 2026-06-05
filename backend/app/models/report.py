from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.session import Base


class ReportTargetType(StrEnum):
    COURSE = "course"
    COMMENT = "comment"
    CHAT_MESSAGE = "chat_message"
    MODULE_CONTENT = "module_content"


class ReportStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"


report_target_type_enum = Enum(
    ReportTargetType,
    name="report_target_type",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)

report_status_enum = Enum(
    ReportStatus,
    name="report_status",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    reporter_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_type: Mapped[ReportTargetType] = mapped_column(report_target_type_enum, nullable=False, index=True)
    course_id: Mapped[UUID | None] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=True, index=True)
    comment_id: Mapped[UUID | None] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    chat_message_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    module_content_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("module_contents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="other")
    reason: Mapped[str] = mapped_column(String(120), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReportStatus] = mapped_column(report_status_enum, nullable=False, default=ReportStatus.OPEN, index=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reporter: Mapped["User"] = relationship(foreign_keys=[reporter_user_id])
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewer_user_id])
    course: Mapped["Course | None"] = relationship()
    comment: Mapped["Comment | None"] = relationship()
    chat_message: Mapped["ChatMessage | None"] = relationship()
    module_content: Mapped["ModuleContent | None"] = relationship()
