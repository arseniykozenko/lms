from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.session import Base


class CourseCollaboratorStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


course_collaborator_status_enum = Enum(
    CourseCollaboratorStatus,
    name="course_collaborator_status",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class CourseCollaborator(Base):
    __tablename__ = "course_collaborators"
    __table_args__ = (UniqueConstraint("course_id", "user_id", name="uq_course_collaborators_course_user"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    invited_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[CourseCollaboratorStatus] = mapped_column(
        course_collaborator_status_enum, nullable=False, default=CourseCollaboratorStatus.PENDING
    )
    invite_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    course: Mapped["Course"] = relationship(back_populates="collaborators")
    user: Mapped["User"] = relationship(foreign_keys=[user_id], back_populates="course_collaborations")
    invited_by: Mapped["User"] = relationship(foreign_keys=[invited_by_user_id])
