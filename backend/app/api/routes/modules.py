from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.security.dependencies import get_current_active_user, require_teacher
from app.schemas.module import ModuleCreate, ModuleRead, ModuleReorderRequest, ModuleUpdate
from app.schemas.user import UserRead
from app.services.modules import ModuleService, get_module_service

router = APIRouter()


@router.post("", response_model=ModuleRead, status_code=201)
def create_module(
    payload: ModuleCreate,
    current_user: UserRead = Depends(require_teacher),
    module_service: ModuleService = Depends(get_module_service),
) -> ModuleRead:
    return module_service.create_module(payload, current_user)


@router.get("/{module_id}", response_model=ModuleRead)
def get_module(
    module_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    module_service: ModuleService = Depends(get_module_service),
) -> ModuleRead:
    return module_service.get_module(module_id, current_user)


@router.patch("/{module_id}", response_model=ModuleRead)
def update_module(
    module_id: UUID,
    payload: ModuleUpdate,
    current_user: UserRead = Depends(require_teacher),
    module_service: ModuleService = Depends(get_module_service),
) -> ModuleRead:
    return module_service.update_module(module_id, payload, current_user)


@router.post("/course/{course_id}/reorder", response_model=list[ModuleRead])
def reorder_modules(
    course_id: UUID,
    payload: ModuleReorderRequest,
    current_user: UserRead = Depends(require_teacher),
    module_service: ModuleService = Depends(get_module_service),
) -> list[ModuleRead]:
    return module_service.reorder_modules(course_id, payload, current_user)
