from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db.session import get_db
from app.core.security.password import hash_password, verify_password
from app.core.security.tokens import create_access_token
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, payload: UserCreate) -> TokenResponse:
        normalized_email = str(payload.email).strip().lower()
        existing = self.users.get_by_email(normalized_email)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

        user = self.users.create(
            first_name=payload.first_name,
            second_name=payload.second_name,
            email=normalized_email,
            password_hash=hash_password(payload.password),
            role=payload.role,
        )
        self.db.commit()
        self.db.refresh(user)
        return self._build_auth_response(user)

    def login(self, payload: LoginRequest) -> TokenResponse:
        normalized_email = str(payload.email).strip().lower()
        user = self.users.get_by_email(normalized_email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        if not user.is_active:
            if user.blocked_until is not None and user.blocked_until > datetime.now(UTC):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is temporarily blocked")
            if user.blocked_until is None and user.blocked_reason:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is blocked")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

        return self._build_auth_response(user)

    def _build_auth_response(self, user) -> TokenResponse:
        access_token, _ = create_access_token(str(user.id))
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserRead.model_validate(user),
        )


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)
