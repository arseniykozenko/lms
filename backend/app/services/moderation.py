from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.models.report import Report, ReportStatus, ReportTargetType
from app.repositories.chat import ChatRepository
from app.repositories.comment import CommentRepository
from app.repositories.course import CourseRepository
from app.repositories.report import ReportRepository
from app.repositories.module_content import ModuleContentRepository
from app.schemas.report import ReportCreate, ReportRead, ReportReviewUpdate
from app.schemas.user import UserRead
from app.services.admin_audit import AdminAuditService, get_admin_audit_service
from app.services.notifications import NotificationService, get_notification_service


class ModerationService:
    CLOSED_REPORT_RETENTION_DAYS = 3

    def __init__(self, db: Session, notifications: NotificationService, audit: AdminAuditService) -> None:
        self.db = db
        self.reports = ReportRepository(db)
        self.courses = CourseRepository(db)
        self.comments = CommentRepository(db)
        self.chat = ChatRepository(db)
        self.module_contents = ModuleContentRepository(db)
        self.notifications = notifications
        self.audit = audit

    def create_report(self, payload: ReportCreate, current_user: UserRead) -> ReportRead:
        self._validate_target_exists(payload)
        report = Report(
            reporter_user_id=current_user.id,
            target_type=payload.target_type,
            course_id=payload.course_id,
            comment_id=payload.comment_id,
            chat_message_id=payload.chat_message_id,
            module_content_id=payload.module_content_id,
            category=payload.category.strip().lower(),
            reason=payload.reason.strip(),
            details=payload.details.strip() if payload.details else None,
        )
        duplicate = self.reports.get_open_duplicate_for_reporter(report)
        if duplicate is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have an active report for this target")
        self.reports.create(report)
        self.db.commit()
        created = self.reports.get_by_id(report.id)
        if created is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create report")
        return self._serialize_report(created)

    def list_reports(self, *, status_value: ReportStatus | None = None) -> list[ReportRead]:
        self._cleanup_closed_reports()
        return [self._serialize_report(item) for item in self.reports.list_all(status=status_value)]

    def review_report(self, report_id: UUID, payload: ReportReviewUpdate, current_user: UserRead) -> ReportRead:
        report = self.reports.get_by_id(report_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        report.status = payload.status
        report.resolution_note = payload.resolution_note
        report.reviewer_user_id = current_user.id
        report.reviewed_at = datetime.now(UTC)
        self.db.commit()
        self.audit.log_action(
            actor=current_user,
            action="admin_review_report",
            target_type="report",
            target_id=str(report.id),
            details_json={"status": payload.status.value, "resolution_note": payload.resolution_note},
        )
        if report.reporter_user_id != current_user.id:
            self.notifications.create_admin_report_reviewed_notification(
                recipient_user_id=report.reporter_user_id,
                report_id=report.id,
                status=payload.status.value,
                resolution_note=payload.resolution_note,
            )
        refreshed = self.reports.get_by_id(report.id)
        if refreshed is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to review report")
        return self._serialize_report(refreshed)

    def _serialize_report(self, report: Report) -> ReportRead:
        link_url = None
        if report.course_id is not None:
            link_url = f"/courses/{report.course_id}"
        elif report.comment is not None:
            link_url = f"/modules/{report.comment.module_id}"
        elif report.module_content_id is not None and report.module_content is not None:
            link_url = f"/modules/{report.module_content.module_id}/content/{report.module_content_id}"
        return ReportRead.model_validate(report).model_copy(update={"link_url": link_url})

    def hide_course(self, course_id: UUID, current_user: UserRead) -> None:
        course = self.courses.get_by_id(course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        course.is_published = False
        self.db.commit()
        self.audit.log_action(
            actor=current_user,
            action="admin_hide_course",
            target_type="course",
            target_id=str(course.id),
            details_json={"course_title": course.title},
        )
        if course.author_id != current_user.id:
            self.notifications.create_admin_course_hidden_notification(
                recipient_user_id=course.author_id,
                course_id=course.id,
                course_title=course.title,
            )

    def restore_course(self, course_id: UUID, current_user: UserRead) -> None:
        course = self.courses.get_by_id(course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        course.is_published = True
        self.db.commit()
        self.audit.log_action(
            actor=current_user,
            action="admin_restore_course",
            target_type="course",
            target_id=str(course.id),
            details_json={"course_title": course.title},
        )
        if course.author_id != current_user.id:
            self.notifications.create_admin_course_restored_notification(
                recipient_user_id=course.author_id,
                course_id=course.id,
                course_title=course.title,
            )

    def hide_comment(self, comment_id: UUID, current_user: UserRead) -> None:
        comment = self.comments.get_by_id(comment_id)
        if comment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        comment.is_deleted = True
        self.db.commit()
        self.audit.log_action(
            actor=current_user,
            action="admin_hide_comment",
            target_type="comment",
            target_id=str(comment.id),
            details_json={"module_id": str(comment.module_id)},
        )
        if comment.user_id != current_user.id:
            self.notifications.create_admin_comment_hidden_notification(
                recipient_user_id=comment.user_id,
                module_id=comment.module_id,
            )

    def restore_comment(self, comment_id: UUID, current_user: UserRead) -> None:
        comment = self.comments.get_by_id(comment_id)
        if comment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        comment.is_deleted = False
        self.db.commit()
        self.audit.log_action(
            actor=current_user,
            action="admin_restore_comment",
            target_type="comment",
            target_id=str(comment.id),
            details_json={"module_id": str(comment.module_id)},
        )
        if comment.user_id != current_user.id:
            self.notifications.create_admin_comment_restored_notification(
                recipient_user_id=comment.user_id,
                module_id=comment.module_id,
            )

    def _validate_target_exists(self, payload: ReportCreate) -> None:
        if payload.target_type == ReportTargetType.COURSE:
            if payload.course_id is None or self.courses.get_by_id(payload.course_id) is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
            return
        if payload.target_type == ReportTargetType.COMMENT:
            if payload.comment_id is None or self.comments.get_by_id(payload.comment_id) is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
            return
        if payload.target_type == ReportTargetType.CHAT_MESSAGE:
            if payload.chat_message_id is None or self.chat.get_by_id(payload.chat_message_id) is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat message not found")
            return
        if payload.module_content_id is None or self.module_contents.get_by_id(payload.module_content_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module content not found")

    def _cleanup_closed_reports(self) -> None:
        threshold = datetime.now(UTC) - timedelta(days=self.CLOSED_REPORT_RETENTION_DAYS)
        removed = self.reports.delete_closed_reviewed_before(threshold)
        if removed:
            self.db.commit()


def get_moderation_service(
    db: Session = Depends(get_db),
    notifications: NotificationService = Depends(get_notification_service),
    audit: AdminAuditService = Depends(get_admin_audit_service),
) -> ModerationService:
    return ModerationService(db, notifications, audit)
