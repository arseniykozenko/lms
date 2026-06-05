from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content_progress import ContentProgress
from app.models.module_content import ModuleContent


class ContentProgressRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_and_content(self, user_id: UUID, content_id: UUID) -> ContentProgress | None:
        stmt = select(ContentProgress).where(
            ContentProgress.user_id == user_id,
            ContentProgress.content_id == content_id,
        )
        return self.db.scalar(stmt)

    def mark_viewed(self, user_id: UUID, content_id: UUID) -> ContentProgress:
        record = self.get_by_user_and_content(user_id, content_id)
        if record is None:
            record = ContentProgress(user_id=user_id, content_id=content_id)
            self.db.add(record)
            self.db.flush()
            return record

        record.updated_at = datetime.now(UTC)
        self.db.flush()
        return record

    def list_viewed_content_ids(self, user_id: UUID, module_ids: list[UUID]) -> set[UUID]:
        if not module_ids:
            return set()

        stmt = (
            select(ContentProgress.content_id)
            .join(ModuleContent, ModuleContent.id == ContentProgress.content_id)
            .where(
                ContentProgress.user_id == user_id,
                ModuleContent.module_id.in_(module_ids),
            )
        )
        return set(self.db.scalars(stmt))

    def latest_activity_at(self, user_id: UUID, module_ids: list[UUID]) -> datetime | None:
        if not module_ids:
            return None

        stmt = (
            select(ContentProgress.updated_at)
            .join(ModuleContent, ModuleContent.id == ContentProgress.content_id)
            .where(
                ContentProgress.user_id == user_id,
                ModuleContent.module_id.in_(module_ids),
            )
            .order_by(ContentProgress.updated_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def recent_activity_count(self, user_id: UUID, module_ids: list[UUID], since: datetime) -> int:
        if not module_ids:
            return 0

        stmt = (
            select(ContentProgress.id)
            .join(ModuleContent, ModuleContent.id == ContentProgress.content_id)
            .where(
                ContentProgress.user_id == user_id,
                ModuleContent.module_id.in_(module_ids),
                ContentProgress.updated_at >= since,
            )
        )
        return len(list(self.db.scalars(stmt)))
