from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.admin_audit_log import AdminAuditLog


class AdminAuditLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, item: AdminAuditLog) -> AdminAuditLog:
        self.db.add(item)
        self.db.flush()
        return item

    def list_recent(self, *, limit: int = 100) -> list[AdminAuditLog]:
        stmt = (
            select(AdminAuditLog)
            .options(joinedload(AdminAuditLog.actor))
            .order_by(AdminAuditLog.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))
