from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.comment import Comment


class CommentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, comment: Comment) -> Comment:
        self.db.add(comment)
        self.db.flush()
        self.db.refresh(comment)
        return comment

    def list_by_module(self, module_id: UUID) -> list[Comment]:
        stmt = (
            select(Comment)
            .options(joinedload(Comment.user))
            .where(Comment.module_id == module_id)
            .order_by(Comment.created_at.asc())
        )
        return list(self.db.scalars(stmt))

    def get_by_id(self, comment_id: UUID) -> Comment | None:
        stmt = select(Comment).options(joinedload(Comment.user)).where(Comment.id == comment_id)
        return self.db.scalar(stmt)

    def has_replies(self, comment_id: UUID) -> bool:
        stmt = select(Comment.id).where(Comment.parent_comment_id == comment_id).limit(1)
        return self.db.scalar(stmt) is not None

    def delete(self, comment: Comment) -> None:
        self.db.delete(comment)
