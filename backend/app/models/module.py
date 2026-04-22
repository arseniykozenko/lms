from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.session import Base


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_published: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    course: Mapped["Course"] = relationship(back_populates="modules")
    contents: Mapped[list["ModuleContent"]] = relationship(back_populates="module", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(back_populates="module", cascade="all, delete-orphan")
    quiz: Mapped["Quiz | None"] = relationship(back_populates="module", cascade="all, delete-orphan", uselist=False)
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="module", cascade="all, delete-orphan")
