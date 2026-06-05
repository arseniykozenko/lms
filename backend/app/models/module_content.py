from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.session import Base


class ModuleContentType(StrEnum):
    TEXT = "text"
    VIDEO = "video"
    PDF = "pdf"
    PRESENTATION = "presentation"
    LINK = "link"


module_content_type_enum = Enum(
    ModuleContentType,
    name="module_content_type",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class ModuleContent(Base):
    __tablename__ = "module_contents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    module_id: Mapped[UUID] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[ModuleContentType] = mapped_column(module_content_type_enum, nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    transcript_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_timestamps_json: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    transcript_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    transcript_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    transcript_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    module: Mapped["Module"] = relationship(back_populates="contents")
    progress_records: Mapped[list["ContentProgress"]] = relationship(back_populates="content", cascade="all, delete-orphan")
