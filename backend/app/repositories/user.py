from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        full_name: str | None = None,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.STUDENT,
    ) -> User:
        user = User(full_name=full_name, email=email, password_hash=password_hash, role=role)
        self.db.add(user)
        self.db.flush()
        return user

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.scalar(stmt)

    def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.scalar(stmt)

    def update_profile(self, user: User, *, full_name: str | None, profile_photo_url: str | None) -> User:
        user.full_name = full_name
        user.profile_photo_url = profile_photo_url
        self.db.flush()
        return user
