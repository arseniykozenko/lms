from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        first_name: str | None = None,
        second_name: str | None = None,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.STUDENT,
    ) -> User:
        user = User(
            first_name=first_name,
            second_name=second_name,
            email=email,
            password_hash=password_hash,
            role=role,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def get_by_email(self, email: str) -> User | None:
        normalized_email = email.strip().lower()
        stmt = select(User).where(func.lower(User.email) == normalized_email)
        return self.db.scalar(stmt)

    def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.scalar(stmt)

    def list_all(self) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc())
        return list(self.db.scalars(stmt))

    def search_teachers(self, *, query: str | None = None, limit: int = 10) -> list[User]:
        stmt = select(User).where(User.role.in_([UserRole.TEACHER, UserRole.ADMIN]))
        if query:
            q = f"%{query.strip()}%"
            stmt = stmt.where((User.email.ilike(q)) | (User.first_name.ilike(q)) | (User.second_name.ilike(q)))
        stmt = stmt.order_by(User.first_name.asc().nulls_last(), User.second_name.asc().nulls_last(), User.email.asc()).limit(limit)
        return list(self.db.scalars(stmt))

    def update_profile(
        self,
        user: User,
        *,
        first_name: str | None,
        second_name: str | None,
        profile_photo_url: str | None,
    ) -> User:
        user.first_name = first_name
        user.second_name = second_name
        user.profile_photo_url = profile_photo_url
        self.db.flush()
        return user
