from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.lib.user_name import get_user_display_name
from app.models.admin_audit_log import AdminAuditLog
from app.repositories.admin_audit_log import AdminAuditLogRepository
from app.schemas.admin_audit_log import AdminAuditLogRead
from app.schemas.user import UserRead


class AdminAuditService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.logs = AdminAuditLogRepository(db)

    def log_action(
        self,
        *,
        actor: UserRead,
        action: str,
        target_type: str,
        target_id: str,
        details_json: dict | None = None,
    ) -> None:
        self.logs.create(
            AdminAuditLog(
                actor_user_id=actor.id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details_json=details_json,
            )
        )
        self.db.commit()

    def list_recent(self, *, limit: int = 100) -> list[AdminAuditLogRead]:
        items = self.logs.list_recent(limit=limit)
        return [
            AdminAuditLogRead(
                id=item.id,
                actor_user_id=item.actor_user_id,
                action=item.action,
                target_type=item.target_type,
                target_id=item.target_id,
                details_json=item.details_json,
                created_at=item.created_at,
                actor_name=get_user_display_name(item.actor) if item.actor else None,
                actor_email=item.actor.email if item.actor else None,
            )
            for item in items
        ]


def get_admin_audit_service(db: Session = Depends(get_db)) -> AdminAuditService:
    return AdminAuditService(db)
