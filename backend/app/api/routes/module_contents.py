from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from app.core.security.dependencies import get_current_active_user, require_teacher
from app.schemas.module_content import (
    ModuleContentLinkCreate,
    ModuleContentRead,
    ModuleContentReorderRequest,
    ModuleContentTextCreate,
    ModuleContentUpdate,
)
from app.schemas.user import UserRead
from app.services.module_contents import ModuleContentService, get_module_content_service

router = APIRouter()


@router.get("/modules/{module_id}/contents", response_model=list[ModuleContentRead])
def list_module_contents(
    module_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    module_content_service: ModuleContentService = Depends(get_module_content_service),
) -> list[ModuleContentRead]:
    return module_content_service.list_module_contents(module_id, current_user)


@router.post("/module-contents/{content_id}/view", status_code=status.HTTP_204_NO_CONTENT)
def mark_module_content_viewed(
    content_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    module_content_service: ModuleContentService = Depends(get_module_content_service),
) -> Response:
    module_content_service.mark_content_viewed(content_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/module-contents/{content_id}/transcribe", response_model=ModuleContentRead)
def transcribe_module_content(
    content_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    module_content_service: ModuleContentService = Depends(get_module_content_service),
) -> ModuleContentRead:
    return module_content_service.generate_transcript(content_id, current_user)


@router.post("/modules/{module_id}/contents/text", response_model=ModuleContentRead, status_code=status.HTTP_201_CREATED)
def create_text_content(
    module_id: UUID,
    payload: ModuleContentTextCreate,
    current_user: UserRead = Depends(require_teacher),
    module_content_service: ModuleContentService = Depends(get_module_content_service),
) -> ModuleContentRead:
    return module_content_service.create_text_content(module_id, payload, current_user)


@router.post("/modules/{module_id}/contents/link", response_model=ModuleContentRead, status_code=status.HTTP_201_CREATED)
def create_link_content(
    module_id: UUID,
    payload: ModuleContentLinkCreate,
    current_user: UserRead = Depends(require_teacher),
    module_content_service: ModuleContentService = Depends(get_module_content_service),
) -> ModuleContentRead:
    return module_content_service.create_link_content(module_id, payload, current_user)


@router.post("/modules/{module_id}/contents/file", response_model=ModuleContentRead, status_code=status.HTTP_201_CREATED)
def create_file_content(
    module_id: UUID,
    title: str = Form(...),
    content_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: UserRead = Depends(require_teacher),
    module_content_service: ModuleContentService = Depends(get_module_content_service),
) -> ModuleContentRead:
    return module_content_service.create_file_content(module_id, title, file, content_type, current_user)


@router.patch("/module-contents/{content_id}", response_model=ModuleContentRead)
def update_module_content(
    content_id: UUID,
    payload: ModuleContentUpdate,
    current_user: UserRead = Depends(require_teacher),
    module_content_service: ModuleContentService = Depends(get_module_content_service),
) -> ModuleContentRead:
    return module_content_service.update_content(content_id, payload, current_user)


@router.post("/module-contents/{content_id}/replace-file", response_model=ModuleContentRead)
def replace_module_content_file(
    content_id: UUID,
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: UserRead = Depends(require_teacher),
    module_content_service: ModuleContentService = Depends(get_module_content_service),
) -> ModuleContentRead:
    return module_content_service.replace_file_content(content_id, title, file, current_user)


@router.delete("/module-contents/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module_content(
    content_id: UUID,
    current_user: UserRead = Depends(require_teacher),
    module_content_service: ModuleContentService = Depends(get_module_content_service),
) -> Response:
    module_content_service.delete_content(content_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/modules/{module_id}/contents/reorder", response_model=list[ModuleContentRead])
def reorder_module_contents(
    module_id: UUID,
    payload: ModuleContentReorderRequest,
    current_user: UserRead = Depends(require_teacher),
    module_content_service: ModuleContentService = Depends(get_module_content_service),
) -> list[ModuleContentRead]:
    return module_content_service.reorder_contents(module_id, payload, current_user)
