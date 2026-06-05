from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.flush()
        return notification

    def get_by_dedupe_key(self, dedupe_key: str) -> Notification | None:
        stmt = select(Notification).where(Notification.dedupe_key == dedupe_key)
        return self.db.scalar(stmt)

    def get_by_id_for_user(self, notification_id: UUID, user_id: UUID) -> Notification | None:
        stmt = select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        notification = self.db.scalar(stmt)
        if notification is None or self._is_dismissed(notification):
            return None
        return notification

    def list_for_user(self, user_id: UUID, *, limit: int = 20) -> list[Notification]:
        fetch_limit = max(limit * 3, 60)
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(fetch_limit)
        )
        items = [item for item in self.db.scalars(stmt) if not self._is_dismissed(item)]
        return items[:limit]

    def unread_count(self, user_id: UUID) -> int:
        stmt = select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        return sum(1 for item in self.db.scalars(stmt) if not self._is_dismissed(item))

    def mark_read(self, notification: Notification) -> Notification:
        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        self.db.flush()
        return notification

    def mark_all_read(self, user_id: UUID) -> None:
        stmt = select(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))
        notifications = list(self.db.scalars(stmt))
        for notification in notifications:
            if self._is_dismissed(notification):
                continue
            notification.is_read = True
            notification.read_at = datetime.now(UTC)
        self.db.flush()

    def delete(self, notification: Notification) -> None:
        data = dict(notification.data_json or {})
        data["dismissed"] = True
        data["dismissed_at"] = datetime.now(UTC).isoformat()
        notification.data_json = data
        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        self.db.flush()

    def delete_read_for_user(self, user_id: UUID) -> int:
        stmt = select(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(True))
        items = list(self.db.scalars(stmt))
        removed = 0
        for item in items:
            if self._is_dismissed(item):
                continue
            data = dict(item.data_json or {})
            data["dismissed"] = True
            data["dismissed_at"] = datetime.now(UTC).isoformat()
            item.data_json = data
            removed += 1
        self.db.flush()
        return removed

    def _is_dismissed(self, notification: Notification) -> bool:
        data = notification.data_json
        return isinstance(data, dict) and bool(data.get("dismissed"))
