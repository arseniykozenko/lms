from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AdminAuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_user_id: UUID
    action: str
    target_type: str
    target_id: str
    details_json: dict | None = None
    created_at: datetime
    actor_name: str | None = None
    actor_email: str | None = None
