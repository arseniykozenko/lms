from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.module import Module


class ModuleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, module: Module) -> Module:
        self.db.add(module)
        self.db.flush()
        return module

    def get_by_id(self, module_id: UUID) -> Module | None:
        return self.db.get(Module, module_id)

    def list_by_course(self, course_id: UUID) -> list[Module]:
        stmt = select(Module).where(Module.course_id == course_id).order_by(Module.position.asc(), Module.created_at.asc())
        return list(self.db.scalars(stmt))

    def get_by_course_and_position(self, course_id: UUID, position: int) -> Module | None:
        stmt = select(Module).where(Module.course_id == course_id, Module.position == position)
        return self.db.scalar(stmt)
