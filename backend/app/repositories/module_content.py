from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.module_content import ModuleContent


class ModuleContentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, content: ModuleContent) -> ModuleContent:
        self.db.add(content)
        self.db.flush()
        return content

    def get_by_id(self, content_id: UUID) -> ModuleContent | None:
        return self.db.get(ModuleContent, content_id)

    def list_by_module(self, module_id: UUID) -> list[ModuleContent]:
        stmt = select(ModuleContent).where(ModuleContent.module_id == module_id).order_by(ModuleContent.position.asc(), ModuleContent.created_at.asc())
        return list(self.db.scalars(stmt))

    def delete(self, content: ModuleContent) -> None:
        self.db.delete(content)
