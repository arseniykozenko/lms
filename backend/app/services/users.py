from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, UploadFile
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.models.course_collaborator import CourseCollaboratorStatus
from app.models.user import UserRole
from app.repositories.course import CourseRepository
from app.repositories.course_collaborator import CourseCollaboratorRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.user import UserRepository
from app.schemas.course import EnrolledCourseRead
from app.schemas.admin_audit_log import AdminAuditLogRead
from app.schemas.user import AdminUserBlockUpdate, AdminUserListItem, TeacherLookupItem, UserRead, UserUpdate
from app.services.admin_audit import AdminAuditService, get_admin_audit_service
from app.services.media import MediaService, get_media_service
from app.services.notifications import NotificationService, get_notification_service
from app.services.progress import ProgressService, get_progress_service


class UserService:
    def __init__(
        self,
        db: Session,
        media: MediaService,
        progress: ProgressService,
        notifications: NotificationService,
        audit: AdminAuditService,
    ) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.courses = CourseRepository(db)
        self.collaborators = CourseCollaboratorRepository(db)
        self.enrollments = EnrollmentRepository(db)
        self.media = media
        self.progress = progress
        self.notifications = notifications
        self.audit = audit

    def get_me(self, current_user: UserRead) -> UserRead:
        user = self.users.get_by_id(current_user.id)
        if user is None:
            return current_user
        return UserRead.model_validate(user)

    def update_me(self, current_user: UserRead, payload: UserUpdate) -> UserRead:
        user = self.users.get_by_id(current_user.id)
        if user is None:
            return current_user
        self.users.update_profile(
            user,
            first_name=payload.first_name or user.first_name,
            second_name=payload.second_name or user.second_name,
            profile_photo_url=self.media.normalize_url(payload.profile_photo_url),
        )
        self.db.commit()
        self.db.refresh(user)
        return UserRead.model_validate(user)

    def upload_profile_photo(self, current_user: UserRead, upload: UploadFile) -> UserRead:
        user = self.users.get_by_id(current_user.id)
        if user is None:
            return current_user
        photo_url = self.media.upload_profile_photo(str(current_user.id), upload)
        self.users.update_profile(
            user,
            first_name=user.first_name,
            second_name=user.second_name,
            profile_photo_url=photo_url,
        )
        self.db.commit()
        self.db.refresh(user)
        return UserRead.model_validate(user)

    def list_my_courses(self, current_user: UserRead) -> list[EnrolledCourseRead]:
        if current_user.role in {UserRole.TEACHER, UserRole.ADMIN}:
            authored_courses = self.courses.list_by_author(current_user.id)
            collaborator_links = self.collaborators.list_by_user(current_user.id)
            collaborated_courses = [
                link.course
                for link in collaborator_links
                if link.status == CourseCollaboratorStatus.ACCEPTED and link.course is not None
            ]
            enrollments = self.enrollments.list_by_user(current_user.id)
            by_id: dict[UUID, tuple] = {}

            for course in [*authored_courses, *collaborated_courses]:
                by_id[course.id] = (course, course.created_at)

            for enrollment in enrollments:
                if enrollment.course is None:
                    continue
                by_id[enrollment.course.id] = (enrollment.course, enrollment.enrolled_at)

            courses = sorted(by_id.values(), key=lambda item: item[1], reverse=True)
            result: list[EnrolledCourseRead] = []
            for course, enrolled_at in courses:
                analytics = self.progress.build_student_course_analytics(course.id, current_user)
                result.append(
                    EnrolledCourseRead(
                        id=course.id,
                        author_id=course.author_id,
                        title=course.title,
                        description=course.description,
                        thumbnail_url=course.thumbnail_url,
                        is_free=course.is_free,
                        is_published=course.is_published,
                        created_at=course.created_at,
                        updated_at=course.updated_at,
                        enrolled_at=enrolled_at,
                        progress=analytics["progress"],
                        progress_status=analytics["progress_status"],
                        last_activity_at=analytics["last_activity_at"],
                        inactivity_days=analytics["inactivity_days"],
                        pending_assignments_count=analytics["pending_assignments_count"],
                        overdue_items_count=analytics["overdue_items_count"],
                        upcoming_deadlines_count=analytics["upcoming_deadlines_count"],
                        average_assignment_score_percent=analytics["average_assignment_score_percent"],
                        average_quiz_score_percent=analytics["average_quiz_score_percent"],
                        recent_completed_items_7d=analytics["recent_completed_items_7d"],
                        engagement_trend=analytics["engagement_trend"],
                    )
                )
            return result

        enrollments = self.enrollments.list_by_user(current_user.id)
        result: list[EnrolledCourseRead] = []
        for enrollment in enrollments:
            course = enrollment.course
            if not course.is_published:
                continue
            analytics = self.progress.build_student_course_analytics(course.id, current_user)
            result.append(
                EnrolledCourseRead(
                    id=course.id,
                    author_id=course.author_id,
                    title=course.title,
                    description=course.description,
                    thumbnail_url=course.thumbnail_url,
                    is_free=course.is_free,
                    is_published=course.is_published,
                    created_at=course.created_at,
                    updated_at=course.updated_at,
                    enrolled_at=enrollment.enrolled_at,
                    progress=analytics["progress"],
                    progress_status=analytics["progress_status"],
                    last_activity_at=analytics["last_activity_at"],
                    inactivity_days=analytics["inactivity_days"],
                    pending_assignments_count=analytics["pending_assignments_count"],
                    overdue_items_count=analytics["overdue_items_count"],
                    upcoming_deadlines_count=analytics["upcoming_deadlines_count"],
                    average_assignment_score_percent=analytics["average_assignment_score_percent"],
                    average_quiz_score_percent=analytics["average_quiz_score_percent"],
                    recent_completed_items_7d=analytics["recent_completed_items_7d"],
                    engagement_trend=analytics["engagement_trend"],
                )
            )
        return result

    def admin_list_users(self) -> list[AdminUserListItem]:
        return [AdminUserListItem.model_validate(item) for item in self.users.list_all()]

    def admin_set_role(self, user_id: UUID, role: UserRole, current_admin: UserRead) -> UserRead:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        previous_role = user.role
        if user.id == current_admin.id and role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You cannot remove your own admin role")
        user.role = role
        self.db.commit()
        self.db.refresh(user)
        self.audit.log_action(
            actor=current_admin,
            action="admin_set_role",
            target_type="user",
            target_id=str(user.id),
            details_json={"old_role": previous_role.value, "new_role": role.value},
        )
        if user.id != current_admin.id:
            self.notifications.create_admin_role_changed_notification(
                recipient_user_id=user.id,
                new_role=role.value,
            )
        return UserRead.model_validate(user)

    def admin_block_user(self, user_id: UUID, payload: AdminUserBlockUpdate, current_admin: UserRead) -> UserRead:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if user.id == current_admin.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You cannot block your own account")
        if payload.blocked_until is not None and payload.blocked_until <= datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="blocked_until must be in the future")
        user.is_active = False
        user.blocked_until = payload.blocked_until
        user.blocked_reason = payload.blocked_reason.strip() if payload.blocked_reason else "Blocked by administrator"
        self.db.commit()
        self.db.refresh(user)
        self.audit.log_action(
            actor=current_admin,
            action="admin_block_user",
            target_type="user",
            target_id=str(user.id),
            details_json={
                "blocked_until": user.blocked_until.isoformat() if user.blocked_until else None,
                "blocked_reason": user.blocked_reason,
            },
        )
        self.notifications.create_admin_account_blocked_notification(
            recipient_user_id=user.id,
            blocked_until=user.blocked_until,
            reason=user.blocked_reason,
        )
        return UserRead.model_validate(user)

    def admin_unblock_user(self, user_id: UUID, current_admin: UserRead) -> UserRead:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.is_active = True
        user.blocked_until = None
        user.blocked_reason = None
        self.db.commit()
        self.db.refresh(user)
        self.audit.log_action(
            actor=current_admin,
            action="admin_unblock_user",
            target_type="user",
            target_id=str(user.id),
        )
        self.notifications.create_admin_account_unblocked_notification(recipient_user_id=user.id)
        return UserRead.model_validate(user)

    def admin_list_audit_logs(self, *, limit: int = 100) -> list[AdminAuditLogRead]:
        return self.audit.list_recent(limit=limit)

    def search_teachers(self, current_user: UserRead, *, query: str | None = None, limit: int = 10) -> list[TeacherLookupItem]:
        if current_user.role not in {UserRole.TEACHER, UserRole.ADMIN}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        items = self.users.search_teachers(query=query, limit=limit)
        return [
            TeacherLookupItem(
                id=item.id,
                first_name=item.first_name,
                second_name=item.second_name,
                email=item.email,
                role=item.role,
            )
            for item in items
            if item.id != current_user.id
        ]


def get_user_service(
    db: Session = Depends(get_db),
    media: MediaService = Depends(get_media_service),
    progress: ProgressService = Depends(get_progress_service),
    notifications: NotificationService = Depends(get_notification_service),
    audit: AdminAuditService = Depends(get_admin_audit_service),
) -> UserService:
    return UserService(db, media, progress, notifications, audit)
