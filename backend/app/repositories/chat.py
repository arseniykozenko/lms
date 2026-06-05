from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.chat_message import ChatMessage


class ChatRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, message: ChatMessage) -> ChatMessage:
        self.db.add(message)
        self.db.flush()
        return message

    def get_by_id(self, message_id: UUID) -> ChatMessage | None:
        return self.db.get(ChatMessage, message_id)

    def list_for_user(self, user_id: UUID) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .options(
                selectinload(ChatMessage.sender),
                selectinload(ChatMessage.recipient),
                selectinload(ChatMessage.course),
            )
            .where(or_(ChatMessage.sender_id == user_id, ChatMessage.recipient_id == user_id))
            .order_by(ChatMessage.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def list_for_pair(self, user_id: UUID, partner_id: UUID, *, limit: int = 100) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .options(
                selectinload(ChatMessage.sender),
                selectinload(ChatMessage.recipient),
                selectinload(ChatMessage.course),
            )
            .where(
                or_(
                    (ChatMessage.sender_id == user_id) & (ChatMessage.recipient_id == partner_id),
                    (ChatMessage.sender_id == partner_id) & (ChatMessage.recipient_id == user_id),
                )
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def mark_read_for_pair(self, user_id: UUID, partner_id: UUID) -> None:
        messages = self.list_for_pair(user_id, partner_id, limit=500)
        now = datetime.now(UTC)
        for message in messages:
            if message.recipient_id == user_id and not message.is_read:
                message.is_read = True
                message.read_at = now
        self.db.flush()
