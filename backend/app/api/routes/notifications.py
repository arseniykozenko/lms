from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.core.security.dependencies import get_current_active_user
from app.schemas.notification import NotificationListResponse, NotificationRead
from app.schemas.user import UserRead
from app.services.notifications import NotificationService, get_notification_service

router = APIRouter()


@router.get("/me/notifications", response_model=NotificationListResponse)
def list_my_notifications(
    current_user: UserRead = Depends(get_current_active_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
    return notification_service.list_my_notifications(current_user)


@router.post("/me/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_notifications_read(
    current_user: UserRead = Depends(get_current_active_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> Response:
    notification_service.mark_all_read(current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/me/notifications/{notification_id}/read", response_model=NotificationRead | None)
def mark_notification_read(
    notification_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationRead | None:
    return notification_service.mark_read(notification_id, current_user)


@router.delete("/me/notifications/read", status_code=status.HTTP_204_NO_CONTENT)
def delete_read_notifications(
    current_user: UserRead = Depends(get_current_active_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> Response:
    notification_service.delete_read_notifications(current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/me/notifications/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> Response:
    notification_service.delete_notification(notification_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
