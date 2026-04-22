from fastapi import APIRouter, Depends, File, UploadFile

from app.core.security.dependencies import get_current_active_user
from app.schemas.course import EnrolledCourseRead
from app.schemas.user import UserRead, UserUpdate
from app.services.users import UserService, get_user_service

router = APIRouter()


@router.get("/me", response_model=UserRead)
def get_me(
    current_user: UserRead = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    return user_service.get_me(current_user)


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: UserUpdate,
    current_user: UserRead = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    return user_service.update_me(current_user, payload)


@router.post("/me/photo", response_model=UserRead)
def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: UserRead = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    return user_service.upload_profile_photo(current_user, file)


@router.get("/me/courses", response_model=list[EnrolledCourseRead])
def list_my_courses(
    current_user: UserRead = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> list[EnrolledCourseRead]:
    return user_service.list_my_courses(current_user)
