from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.security.dependencies import get_current_active_user, require_admin
from app.models.report import ReportStatus
from app.schemas.report import ReportCreate, ReportRead, ReportReviewUpdate
from app.schemas.user import UserRead
from app.services.moderation import ModerationService, get_moderation_service

router = APIRouter()


@router.post("/reports", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: ReportCreate,
    current_user: UserRead = Depends(get_current_active_user),
    moderation_service: ModerationService = Depends(get_moderation_service),
) -> ReportRead:
    return moderation_service.create_report(payload, current_user)


@router.get("/admin/reports", response_model=list[ReportRead])
def list_reports(
    status_value: ReportStatus | None = Query(default=None, alias="status"),
    _: UserRead = Depends(require_admin),
    moderation_service: ModerationService = Depends(get_moderation_service),
) -> list[ReportRead]:
    return moderation_service.list_reports(status_value=status_value)


@router.patch("/admin/reports/{report_id}", response_model=ReportRead)
def review_report(
    report_id: UUID,
    payload: ReportReviewUpdate,
    current_user: UserRead = Depends(require_admin),
    moderation_service: ModerationService = Depends(get_moderation_service),
) -> ReportRead:
    return moderation_service.review_report(report_id, payload, current_user)


@router.post("/admin/courses/{course_id}/hide", status_code=status.HTTP_204_NO_CONTENT)
def hide_course(
    course_id: UUID,
    current_user: UserRead = Depends(require_admin),
    moderation_service: ModerationService = Depends(get_moderation_service),
) -> Response:
    moderation_service.hide_course(course_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/admin/courses/{course_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
def restore_course(
    course_id: UUID,
    current_user: UserRead = Depends(require_admin),
    moderation_service: ModerationService = Depends(get_moderation_service),
) -> Response:
    moderation_service.restore_course(course_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/admin/comments/{comment_id}/hide", status_code=status.HTTP_204_NO_CONTENT)
def hide_comment(
    comment_id: UUID,
    current_user: UserRead = Depends(require_admin),
    moderation_service: ModerationService = Depends(get_moderation_service),
) -> Response:
    moderation_service.hide_comment(comment_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/admin/comments/{comment_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
def restore_comment(
    comment_id: UUID,
    current_user: UserRead = Depends(require_admin),
    moderation_service: ModerationService = Depends(get_moderation_service),
) -> Response:
    moderation_service.restore_comment(comment_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
