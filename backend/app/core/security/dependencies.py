from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.core.security.tokens import bearer_scheme, decode_access_token
from app.models.user import UserRole
from app.repositories.user import UserRepository
from app.schemas.user import UserRead


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserRead:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials)
    user = UserRepository(db).get_by_id(UUID(payload.sub))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return UserRead.model_validate(user)


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserRead | None:
    if credentials is None:
        return None
    payload = decode_access_token(credentials.credentials)
    user = UserRepository(db).get_by_id(UUID(payload.sub))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return UserRead.model_validate(user)


def get_current_active_user(current_user: UserRead = Depends(get_current_user)) -> UserRead:
    if not current_user.is_active:
        if current_user.blocked_until is not None and current_user.blocked_until > datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is temporarily blocked")
        if current_user.blocked_until is None and current_user.blocked_reason:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is blocked")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def require_teacher(current_user: UserRead = Depends(get_current_active_user)) -> UserRead:
    if current_user.role not in {UserRole.TEACHER, UserRole.ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher permissions required")
    return current_user


def require_admin(current_user: UserRead = Depends(get_current_active_user)) -> UserRead:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required")
    return current_user
