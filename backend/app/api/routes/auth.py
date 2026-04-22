from fastapi import APIRouter, Depends, status

from app.core.security.dependencies import get_current_active_user
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth import AuthService, get_auth_service

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, auth_service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return auth_service.register(payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, auth_service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return auth_service.login(payload)


@router.get("/me", response_model=UserRead)
def me(current_user: UserRead = Depends(get_current_active_user)) -> UserRead:
    return current_user
