from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.chat_group import ChatGroup, ChatGroupMember, ChatGroupMessage


class ChatGroupRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_group(self, item: ChatGroup) -> ChatGroup:
        self.db.add(item)
        self.db.flush()
        return item

    def create_member(self, item: ChatGroupMember) -> ChatGroupMember:
        self.db.add(item)
        self.db.flush()
        return item

    def create_message(self, item: ChatGroupMessage) -> ChatGroupMessage:
        self.db.add(item)
        self.db.flush()
        return item

    def list_groups_for_user(self, user_id: UUID) -> list[ChatGroup]:
        stmt = (
            select(ChatGroup)
            .join(ChatGroupMember, ChatGroupMember.group_id == ChatGroup.id)
            .options(selectinload(ChatGroup.members).selectinload(ChatGroupMember.user))
            .where(ChatGroupMember.user_id == user_id)
            .order_by(ChatGroup.updated_at.desc())
        )
        return list(self.db.scalars(stmt))

    def get_group_for_user(self, group_id: UUID, user_id: UUID) -> ChatGroup | None:
        stmt = (
            select(ChatGroup)
            .join(ChatGroupMember, ChatGroupMember.group_id == ChatGroup.id)
            .options(selectinload(ChatGroup.members).selectinload(ChatGroupMember.user))
            .where(ChatGroup.id == group_id, ChatGroupMember.user_id == user_id)
        )
        return self.db.scalar(stmt)

    def list_messages(self, group_id: UUID, limit: int = 100) -> list[ChatGroupMessage]:
        stmt = (
            select(ChatGroupMessage)
            .options(selectinload(ChatGroupMessage.sender))
            .where(ChatGroupMessage.group_id == group_id)
            .order_by(ChatGroupMessage.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))
