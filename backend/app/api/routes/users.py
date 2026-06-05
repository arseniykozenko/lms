from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.core.security.dependencies import get_current_active_user, require_admin
from app.schemas.admin_audit_log import AdminAuditLogRead
from app.schemas.course import EnrolledCourseRead
from app.schemas.user import AdminUserBlockUpdate, AdminUserListItem, AdminUserRoleUpdate, TeacherLookupItem, UserRead, UserUpdate
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


@router.get("/teachers/search", response_model=list[TeacherLookupItem])
def search_teachers(
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=10, ge=1, le=20),
    current_user: UserRead = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> list[TeacherLookupItem]:
    return user_service.search_teachers(current_user, query=q, limit=limit)


@router.get("/admin/users", response_model=list[AdminUserListItem])
def admin_list_users(
    _: UserRead = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> list[AdminUserListItem]:
    return user_service.admin_list_users()


@router.post("/admin/users/{user_id}/role", response_model=UserRead)
def admin_set_role(
    user_id: UUID,
    payload: AdminUserRoleUpdate,
    current_user: UserRead = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    return user_service.admin_set_role(user_id, payload.role, current_user)


@router.post("/admin/users/{user_id}/block", response_model=UserRead)
def admin_block_user(
    user_id: UUID,
    payload: AdminUserBlockUpdate,
    current_user: UserRead = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    return user_service.admin_block_user(user_id, payload, current_user)


@router.post("/admin/users/{user_id}/unblock", response_model=UserRead)
def admin_unblock_user(
    user_id: UUID,
    current_user: UserRead = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    return user_service.admin_unblock_user(user_id, current_user)


@router.get("/admin/audit-logs", response_model=list[AdminAuditLogRead])
def admin_list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    _: UserRead = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> list[AdminAuditLogRead]:
    return user_service.admin_list_audit_logs(limit=limit)
