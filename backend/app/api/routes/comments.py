from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.security.dependencies import get_current_active_user
from app.schemas.comment import CommentCreate, CommentRead
from app.schemas.user import UserRead
from app.services.comments import CommentService, get_comment_service

router = APIRouter()


@router.post("/modules/{module_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
def create_comment(
    module_id: UUID,
    payload: CommentCreate,
    current_user: UserRead = Depends(get_current_active_user),
    comment_service: CommentService = Depends(get_comment_service),
) -> CommentRead:
    return comment_service.create_comment(module_id, payload, current_user)


@router.get("/modules/{module_id}/comments", response_model=list[CommentRead])
def list_comments(
    module_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserRead = Depends(get_current_active_user),
    comment_service: CommentService = Depends(get_comment_service),
) -> list[CommentRead]:
    return comment_service.list_comments(module_id, current_user, limit=limit, offset=offset)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    comment_service: CommentService = Depends(get_comment_service),
) -> Response:
    comment_service.delete_comment(comment_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
