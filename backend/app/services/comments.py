from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.lib.user_name import get_user_display_name
from app.models.comment import Comment
from app.models.user import UserRole
from app.repositories.comment import CommentRepository
from app.repositories.module import ModuleRepository
from app.schemas.comment import CommentCreate, CommentDeleteResponse, CommentRead
from app.schemas.user import UserRead
from app.services.courses import CourseService, get_course_service
from app.services.notifications import NotificationService, get_notification_service


class CommentService:
    def __init__(self, db: Session, courses: CourseService, notifications: NotificationService) -> None:
        self.db = db
        self.comments = CommentRepository(db)
        self.modules = ModuleRepository(db)
        self.courses = courses
        self.notifications = notifications

    def create_comment(self, module_id: UUID, payload: CommentCreate, current_user: UserRead) -> CommentRead:
        module = self._get_module_or_404(module_id)
        if not self.courses.has_course_access(module.course_id, current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not enrolled in this course")
        parent_comment_id = None
        parent_comment = None
        if payload.parent_comment_id is not None:
            parent_comment = self.comments.get_by_id(payload.parent_comment_id)
            if parent_comment is None or parent_comment.module_id != module_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent comment not found")
            if parent_comment.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You cannot reply to a deleted comment",
                )
            parent_comment_id = parent_comment.id

        comment = Comment(
            user_id=current_user.id,
            module_id=module_id,
            parent_comment_id=parent_comment_id,
            content=payload.content,
        )
        created = self.comments.create(comment)
        self.db.commit()
        self.db.refresh(created)
        if parent_comment_id is not None and parent_comment is not None and parent_comment.user_id != current_user.id:
            actor_name = get_user_display_name(current_user)
            self.notifications.create_comment_reply_notification(
                parent_comment.user_id,
                module_id=module_id,
                actor_name=actor_name,
            )
        elif parent_comment_id is None and current_user.role in {UserRole.TEACHER, UserRole.ADMIN}:
            actor_name = get_user_display_name(current_user)
            self.notifications.create_teacher_announcement_notifications(
                module.course_id,
                module_id=module_id,
                comment_id=created.id,
                actor_name=actor_name,
                content=created.content,
            )
        return CommentRead.model_validate(created)

    def list_comments(self, module_id: UUID, current_user: UserRead, *, limit: int, offset: int) -> list[CommentRead]:
        module = self._get_module_or_404(module_id)
        if not self.courses.has_course_access(module.course_id, current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not enrolled in this course")
        comments = self.comments.list_by_module(module_id)
        comments_by_id: dict[UUID, CommentRead] = {}
        roots: list[CommentRead] = []

        for comment in comments:
            comments_by_id[comment.id] = CommentRead(
                id=comment.id,
                module_id=comment.module_id,
                parent_comment_id=comment.parent_comment_id,
                content="Сообщение удалено" if comment.is_deleted else comment.content,
                is_deleted=comment.is_deleted,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
                user=UserRead.model_validate(comment.user),
                replies=[],
            )

        for comment in comments:
            current = comments_by_id[comment.id]
            if comment.parent_comment_id and comment.parent_comment_id in comments_by_id:
                comments_by_id[comment.parent_comment_id].replies.append(current)
            else:
                roots.append(current)

        roots.sort(key=lambda item: item.created_at, reverse=True)
        if offset:
            roots = roots[offset:]
        if limit:
            roots = roots[:limit]
        return roots

    def delete_comment(self, comment_id: UUID, current_user: UserRead) -> CommentDeleteResponse:
        comment = self.comments.get_by_id(comment_id)
        if comment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        module = self._get_module_or_404(comment.module_id)
        if not self.courses.has_course_access(module.course_id, current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not enrolled in this course")
        if comment.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can delete only your own comments")
        response = CommentDeleteResponse(id=comment.id, module_id=comment.module_id)
        if self.comments.has_replies(comment.id):
            comment.content = ""
            comment.is_deleted = True
        else:
            parent_comment_id = comment.parent_comment_id
            self.comments.delete(comment)
            self.db.flush()
            self._cleanup_deleted_ancestors(parent_comment_id)
        self.db.commit()
        return response

    def _cleanup_deleted_ancestors(self, comment_id: UUID | None) -> None:
        current_comment_id = comment_id
        while current_comment_id is not None:
            current_comment = self.comments.get_by_id(current_comment_id)
            if current_comment is None:
                return
            if not current_comment.is_deleted or self.comments.has_replies(current_comment.id):
                return
            parent_comment_id = current_comment.parent_comment_id
            self.comments.delete(current_comment)
            self.db.flush()
            current_comment_id = parent_comment_id

    def _get_module_or_404(self, module_id: UUID):
        module = self.modules.get_by_id(module_id)
        if module is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
        return module


def get_comment_service(
    db: Session = Depends(get_db),
    courses: CourseService = Depends(get_course_service),
    notifications: NotificationService = Depends(get_notification_service),
) -> CommentService:
    return CommentService(db, courses, notifications)
