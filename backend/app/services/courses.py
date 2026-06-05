import csv
import io
import zipfile
from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.lib.user_name import get_user_display_name
from app.models.course_collaborator import CourseCollaborator, CourseCollaboratorStatus
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import UserRole
from app.repositories.course_collaborator import CourseCollaboratorRepository
from app.repositories.course import CourseRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.user import UserRepository
from app.schemas.course import (
    CourseCollaboratorInviteCreate,
    CourseCollaboratorRead,
    CourseCreate,
    CourseRead,
    CourseUpdate,
)
from app.schemas.enrollment import CourseStudentEnrollmentRead, EnrollmentRead
from app.schemas.user import UserRead
from app.services.media import MediaService, get_media_service
from app.services.notifications import NotificationService, get_notification_service
from app.services.progress import ProgressService, get_progress_service


class CourseService:
    def __init__(
        self, db: Session, media: MediaService, progress: ProgressService, notifications: NotificationService
    ) -> None:
        self.db = db
        self.courses = CourseRepository(db)
        self.collaborators = CourseCollaboratorRepository(db)
        self.enrollments = EnrollmentRepository(db)
        self.users = UserRepository(db)
        self.media = media
        self.progress = progress
        self.notifications = notifications

    def list_courses(
        self,
        current_user: UserRead | None,
        *,
        query: str | None = None,
        category: str | None = None,
        is_free: bool | None = None,
    ) -> list[CourseRead]:
        courses = self.courses.list_filtered(query=query, category=category, is_free=is_free)
        if current_user is None:
            return [CourseRead.model_validate(course) for course in courses if course.is_published]
        visible = [
            course
            for course in courses
            if course.is_published
            or course.author_id == current_user.id
            or current_user.role == UserRole.ADMIN
            or self.is_course_collaborator(course.id, current_user.id)
        ]
        return [CourseRead.model_validate(course) for course in visible]

    def get_course(self, course_id: UUID, current_user: UserRead) -> CourseRead:
        course = self._get_course_or_404(course_id)
        if (
            not course.is_published
            and course.author_id != current_user.id
            and current_user.role != UserRole.ADMIN
            and not self.is_course_collaborator(course.id, current_user.id)
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Course is not published")
        return CourseRead.model_validate(course)

    def list_categories(self, current_user: UserRead | None) -> list[str]:
        categories = self.courses.list_distinct_categories()
        if current_user is None:
            visible_courses = self.courses.list_filtered()
            visible_categories = {(course.category or "").strip() for course in visible_courses if course.category and course.is_published}
            return sorted(visible_categories)
        if current_user.role == UserRole.ADMIN:
            return categories

        visible_courses = self.courses.list_filtered()
        visible_categories = {
            (course.category or "").strip()
            for course in visible_courses
            if course.category
            and (course.is_published or course.author_id == current_user.id or self.is_course_collaborator(course.id, current_user.id))
        }
        return sorted(visible_categories)

    def create_course(self, payload: CourseCreate, current_user: UserRead) -> CourseRead:
        if current_user.role not in {UserRole.TEACHER, UserRole.ADMIN}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can create courses")

        course = Course(
            author_id=current_user.id,
            title=payload.title,
            description=payload.description,
            category=payload.category.strip() if payload.category else None,
            thumbnail_url=self.media.normalize_url(payload.thumbnail_url),
            is_free=True,
            is_published=payload.is_published,
        )
        self.courses.create(course)
        self.db.commit()
        self.db.refresh(course)
        return CourseRead.model_validate(course)

    def update_course(self, course_id: UUID, payload: CourseUpdate, current_user: UserRead) -> CourseRead:
        course = self._get_course_for_management(course_id, current_user)
        for field in ("title", "description", "is_published"):
            value = getattr(payload, field)
            if value is not None:
                setattr(course, field, value)
        course.is_free = True
        if payload.category is not None:
            course.category = payload.category.strip() or None
        if payload.thumbnail_url is not None:
            course.thumbnail_url = self.media.normalize_url(payload.thumbnail_url)
        self.db.commit()
        self.db.refresh(course)
        return CourseRead.model_validate(course)

    def export_course_students_csv(self, course_id: UUID, current_user: UserRead) -> str:
        course = self._get_course_for_management(course_id, current_user)
        enrollments = self.enrollments.list_by_course(course.id)

        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter=";", lineterminator="\r\n")
        writer.writerow(
            [
                "student_name",
                "email",
                "progress_percent",
                "progress_status",
                "completed_items",
                "total_items",
                "viewed_contents",
                "total_contents",
                "completed_assignments",
                "total_assignments",
                "completed_quizzes",
                "total_quizzes",
                "completed_modules",
                "total_modules",
                "risk_level",
                "risk_score",
                "inactivity_days",
                "pending_assignments",
                "passed_quizzes",
                "failed_quizzes",
                "overdue_items",
                "upcoming_deadlines",
                "late_submissions",
                "avg_assignment_score_percent",
                "avg_quiz_score_percent",
                "recent_activity_count_7d",
                "recent_completed_items_7d",
                "pseudo_activity",
                "engagement_trend",
                "last_activity_at",
            ]
        )
        for enrollment in enrollments:
            user = UserRead.model_validate(enrollment.user)
            analytics = self.progress.build_student_course_analytics(course.id, user)
            progress = analytics["progress"]
            writer.writerow(
                [
                    get_user_display_name(user),
                    user.email,
                    progress.progress_percent,
                    analytics["progress_status"],
                    progress.completed_items,
                    progress.total_items,
                    progress.viewed_contents,
                    progress.total_contents,
                    progress.completed_assignments,
                    progress.total_assignments,
                    progress.completed_quizzes,
                    progress.total_quizzes,
                    progress.completed_modules,
                    progress.total_modules,
                    analytics["risk_level"],
                    analytics["risk_score"],
                    analytics["inactivity_days"] if analytics["inactivity_days"] is not None else 0,
                    analytics["pending_assignments_count"],
                    analytics["passed_quizzes_count"],
                    analytics["failed_quizzes_count"],
                    analytics["overdue_items_count"],
                    analytics["upcoming_deadlines_count"],
                    analytics["late_submissions_count"],
                    analytics["average_assignment_score_percent"] if analytics["average_assignment_score_percent"] is not None else 0,
                    analytics["average_quiz_score_percent"] if analytics["average_quiz_score_percent"] is not None else 0,
                    analytics["recent_activity_count_7d"],
                    analytics["recent_completed_items_7d"],
                    "1" if analytics["pseudo_activity"] else "0",
                    analytics["engagement_trend"],
                    analytics["last_activity_at"].isoformat() if analytics["last_activity_at"] else "",
                ]
            )

        return output.getvalue()

    def export_course_analytics_zip(self, course_id: UUID, current_user: UserRead) -> bytes:
        course = self._get_course_for_management(course_id, current_user)
        enrollments = self.enrollments.list_by_course(course.id)

        student_rows: list[dict] = []
        module_map: dict[str, dict] = {}
        progress_values: list[int] = []
        risk_scores: list[int] = []
        completed_students = 0
        active_students = 0
        high_risk = 0
        medium_risk = 0
        low_risk = 0
        total_pending = 0
        total_overdue = 0
        total_upcoming = 0
        total_late = 0
        total_recent_activity = 0
        total_recent_completions = 0
        trend_growing = 0
        trend_stable = 0
        trend_stalled = 0
        inactivity_values: list[int] = []
        assignment_score_values: list[int] = []
        quiz_score_values: list[int] = []

        for enrollment in enrollments:
            user = UserRead.model_validate(enrollment.user)
            analytics = self.progress.build_student_course_analytics(course.id, user)
            progress = analytics["progress"]
            progress_values.append(progress.progress_percent)
            risk_scores.append(analytics["risk_score"])
            total_pending += analytics["pending_assignments_count"]
            total_overdue += analytics["overdue_items_count"]
            total_upcoming += analytics["upcoming_deadlines_count"]
            total_late += analytics["late_submissions_count"]
            total_recent_activity += analytics["recent_activity_count_7d"]
            total_recent_completions += analytics["recent_completed_items_7d"]

            inactivity_days = analytics["inactivity_days"] if analytics["inactivity_days"] is not None else 0
            inactivity_values.append(inactivity_days)

            if analytics["average_assignment_score_percent"] is not None:
                assignment_score_values.append(analytics["average_assignment_score_percent"])
            if analytics["average_quiz_score_percent"] is not None:
                quiz_score_values.append(analytics["average_quiz_score_percent"])

            if analytics["progress_status"] == "completed":
                completed_students += 1
            if analytics["progress_status"] != "not_started":
                active_students += 1

            if analytics["risk_level"] == "high":
                high_risk += 1
            elif analytics["risk_level"] == "medium":
                medium_risk += 1
            else:
                low_risk += 1

            if analytics["engagement_trend"] == "growing":
                trend_growing += 1
            elif analytics["engagement_trend"] == "stalled":
                trend_stalled += 1
            else:
                trend_stable += 1

            student_rows.append(
                {
                    "student_name": get_user_display_name(user),
                    "email": user.email,
                    "progress_percent": progress.progress_percent,
                    "progress_status": analytics["progress_status"],
                    "completed_items": progress.completed_items,
                    "total_items": progress.total_items,
                    "viewed_contents": progress.viewed_contents,
                    "total_contents": progress.total_contents,
                    "completed_assignments": progress.completed_assignments,
                    "total_assignments": progress.total_assignments,
                    "completed_quizzes": progress.completed_quizzes,
                    "total_quizzes": progress.total_quizzes,
                    "completed_modules": progress.completed_modules,
                    "total_modules": progress.total_modules,
                    "risk_level": analytics["risk_level"],
                    "risk_score": analytics["risk_score"],
                    "inactivity_days": inactivity_days,
                    "pending_assignments": analytics["pending_assignments_count"],
                    "passed_quizzes": analytics["passed_quizzes_count"],
                    "failed_quizzes": analytics["failed_quizzes_count"],
                    "overdue_items": analytics["overdue_items_count"],
                    "upcoming_deadlines": analytics["upcoming_deadlines_count"],
                    "late_submissions": analytics["late_submissions_count"],
                    "avg_assignment_score_percent": analytics["average_assignment_score_percent"] or 0,
                    "avg_quiz_score_percent": analytics["average_quiz_score_percent"] or 0,
                    "recent_activity_count_7d": analytics["recent_activity_count_7d"],
                    "recent_completed_items_7d": analytics["recent_completed_items_7d"],
                    "pseudo_activity": analytics["pseudo_activity"],
                    "engagement_trend": analytics["engagement_trend"],
                    "last_activity_at": analytics["last_activity_at"].isoformat() if analytics["last_activity_at"] else "",
                }
            )

            for module in progress.modules:
                entry = module_map.get(module.module_id)
                if entry is None:
                    entry = {
                        "module_id": module.module_id,
                        "module_title": module.module_title,
                        "student_count": 0,
                        "total_progress": 0,
                        "started_count": 0,
                        "completed_count": 0,
                    }
                    module_map[module.module_id] = entry
                entry["student_count"] += 1
                entry["total_progress"] += module.progress_percent
                if module.progress_percent > 0:
                    entry["started_count"] += 1
                if module.progress_percent == 100:
                    entry["completed_count"] += 1

        students_count = len(student_rows)
        average_progress = round(sum(progress_values) / students_count) if students_count else 0
        sorted_progress = sorted(progress_values)
        median_progress = sorted_progress[students_count // 2] if students_count else 0
        average_risk_score = round(sum(risk_scores) / students_count) if students_count else 0
        average_inactivity_days = round(sum(inactivity_values) / students_count) if students_count else 0
        average_assignment_score = (
            round(sum(assignment_score_values) / len(assignment_score_values)) if assignment_score_values else 0
        )
        average_quiz_score = round(sum(quiz_score_values) / len(quiz_score_values)) if quiz_score_values else 0

        summary_csv = io.StringIO(newline="")
        summary_writer = csv.writer(summary_csv, delimiter=";", lineterminator="\r\n")
        summary_writer.writerow(["metric", "value"])
        summary_writer.writerow(["course_id", str(course.id)])
        summary_writer.writerow(["course_title", course.title])
        summary_writer.writerow(["author_id", str(course.author_id)])
        summary_writer.writerow(["category", course.category or ""])
        summary_writer.writerow(["is_published", str(course.is_published)])
        summary_writer.writerow(["created_at", course.created_at.isoformat()])
        summary_writer.writerow(["students_total", students_count])
        summary_writer.writerow(["students_active", active_students])
        summary_writer.writerow(["students_completed", completed_students])
        summary_writer.writerow(["average_progress_percent", average_progress])
        summary_writer.writerow(["median_progress_percent", median_progress])
        summary_writer.writerow(["average_risk_score", average_risk_score])
        summary_writer.writerow(["average_inactivity_days", average_inactivity_days])
        summary_writer.writerow(["risk_low_count", low_risk])
        summary_writer.writerow(["risk_medium_count", medium_risk])
        summary_writer.writerow(["risk_high_count", high_risk])
        summary_writer.writerow(["pending_assignments_total", total_pending])
        summary_writer.writerow(["overdue_items_total", total_overdue])
        summary_writer.writerow(["upcoming_deadlines_total", total_upcoming])
        summary_writer.writerow(["late_submissions_total", total_late])
        summary_writer.writerow(["recent_activity_events_7d_total", total_recent_activity])
        summary_writer.writerow(["recent_completed_items_7d_total", total_recent_completions])
        summary_writer.writerow(["engagement_growing_count", trend_growing])
        summary_writer.writerow(["engagement_stable_count", trend_stable])
        summary_writer.writerow(["engagement_stalled_count", trend_stalled])
        summary_writer.writerow(["average_assignment_score_percent", average_assignment_score])
        summary_writer.writerow(["average_quiz_score_percent", average_quiz_score])

        students_csv = io.StringIO(newline="")
        students_writer = csv.writer(students_csv, delimiter=";", lineterminator="\r\n")
        students_header = [
            "student_name",
            "email",
            "progress_percent",
            "progress_status",
            "completed_items",
            "total_items",
            "viewed_contents",
            "total_contents",
            "completed_assignments",
            "total_assignments",
            "completed_quizzes",
            "total_quizzes",
            "completed_modules",
            "total_modules",
            "risk_level",
            "risk_score",
            "inactivity_days",
            "pending_assignments",
            "passed_quizzes",
            "failed_quizzes",
            "overdue_items",
            "upcoming_deadlines",
            "late_submissions",
            "avg_assignment_score_percent",
            "avg_quiz_score_percent",
            "recent_activity_count_7d",
            "recent_completed_items_7d",
            "pseudo_activity",
            "engagement_trend",
            "last_activity_at",
        ]
        students_writer.writerow(students_header)
        for row in student_rows:
            students_writer.writerow([row[column] for column in students_header])

        modules_csv = io.StringIO(newline="")
        modules_writer = csv.writer(modules_csv, delimiter=";", lineterminator="\r\n")
        modules_writer.writerow(
            [
                "module_id",
                "module_title",
                "student_count",
                "started_count",
                "completed_count",
                "average_progress_percent",
                "start_rate_percent",
                "completion_rate_percent",
            ]
        )
        for module in sorted(module_map.values(), key=lambda value: value["module_title"]):
            student_count = module["student_count"] or 0
            average_module_progress = round(module["total_progress"] / student_count) if student_count else 0
            start_rate = round((module["started_count"] / student_count) * 100) if student_count else 0
            completion_rate = round((module["completed_count"] / student_count) * 100) if student_count else 0
            modules_writer.writerow(
                [
                    module["module_id"],
                    module["module_title"],
                    student_count,
                    module["started_count"],
                    module["completed_count"],
                    average_module_progress,
                    start_rate,
                    completion_rate,
                ]
            )

        archive = io.BytesIO()
        with zipfile.ZipFile(archive, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("course_summary.csv", f"\ufeff{summary_csv.getvalue()}".encode("utf-8"))
            zip_file.writestr("students_analytics.csv", f"\ufeff{students_csv.getvalue()}".encode("utf-8"))
            zip_file.writestr("modules_analytics.csv", f"\ufeff{modules_csv.getvalue()}".encode("utf-8"))
        return archive.getvalue()

    def delete_course(self, course_id: UUID, current_user: UserRead) -> None:
        course = self._get_course_for_deletion(course_id, current_user)
        self.courses.delete(course)
        self.db.commit()

    def invite_course_collaborator(
        self, course_id: UUID, payload: CourseCollaboratorInviteCreate, current_user: UserRead
    ) -> CourseCollaboratorRead:
        course = self._get_course_for_management(course_id, current_user)
        if current_user.role != UserRole.ADMIN and course.author_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only course author can invite collaborators")

        teacher = self.users.get_by_email(payload.teacher_email.strip().lower())
        if teacher is None or teacher.role not in {UserRole.TEACHER, UserRole.ADMIN}:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
        if teacher.id == course.author_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Author is already course owner")

        collaborator = self.collaborators.get_by_course_and_user(course.id, teacher.id)
        if collaborator is None:
            collaborator = CourseCollaborator(
                course_id=course.id,
                user_id=teacher.id,
                invited_by_user_id=current_user.id,
                status=CourseCollaboratorStatus.PENDING,
                invite_message=(payload.message or "").strip() or None,
            )
            self.collaborators.create(collaborator)
        else:
            collaborator.status = CourseCollaboratorStatus.PENDING
            collaborator.invited_by_user_id = current_user.id
            collaborator.invite_message = (payload.message or "").strip() or None
            collaborator.accepted_at = None
            collaborator.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(collaborator)

        inviter_name = get_user_display_name(current_user)
        invite_message = payload.message.strip() if payload.message else None
        self.notifications.create_course_collaboration_invite_notification(
            recipient_user_id=teacher.id,
            inviter_user_id=current_user.id,
            inviter_name=inviter_name,
            course_id=course.id,
            course_title=course.title,
            message_text=invite_message,
        )
        return self._to_collaborator_read(collaborator)

    def list_course_collaborators(self, course_id: UUID, current_user: UserRead) -> list[CourseCollaboratorRead]:
        self._get_course_for_management(course_id, current_user)
        collaborators = self.collaborators.list_by_course(course_id)
        return [self._to_collaborator_read(item) for item in collaborators]

    def list_my_collaboration_invites(self, current_user: UserRead) -> list[CourseCollaboratorRead]:
        items = self.collaborators.list_by_user(current_user.id, status=CourseCollaboratorStatus.PENDING)
        return [self._to_collaborator_read(item) for item in items]

    def remove_course_collaborator(self, course_id: UUID, collaborator_user_id: UUID, current_user: UserRead) -> None:
        course = self._get_course_for_management(course_id, current_user)
        if current_user.role != UserRole.ADMIN and course.author_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only course author can remove collaborators")
        collaborator = self.collaborators.get_by_course_and_user(course_id, collaborator_user_id)
        if collaborator is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collaborator not found")
        if collaborator.user_id == course.author_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Course author cannot be removed")
        self.db.delete(collaborator)
        self.db.commit()
        remover_name = get_user_display_name(current_user)
        self.notifications.create_course_collaborator_removed_notification(
            recipient_user_id=collaborator_user_id,
            course_id=course.id,
            course_title=course.title,
            remover_name=remover_name,
        )

    def accept_course_collaboration_invite(self, invite_id: UUID, current_user: UserRead) -> CourseCollaboratorRead:
        invite = self._get_invite_for_current_user_or_404(invite_id, current_user)
        invite.status = CourseCollaboratorStatus.ACCEPTED
        invite.accepted_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(invite)
        return self._to_collaborator_read(invite)

    def decline_course_collaboration_invite(self, invite_id: UUID, current_user: UserRead) -> CourseCollaboratorRead:
        invite = self._get_invite_for_current_user_or_404(invite_id, current_user)
        invite.status = CourseCollaboratorStatus.DECLINED
        self.db.commit()
        self.db.refresh(invite)
        return self._to_collaborator_read(invite)

    def upload_thumbnail(self, course_id: UUID, upload: UploadFile, current_user: UserRead) -> CourseRead:
        course = self._get_course_for_management(course_id, current_user)
        course.thumbnail_url = self.media.upload_course_thumbnail(str(course.id), upload)
        self.db.commit()
        self.db.refresh(course)
        return CourseRead.model_validate(course)

    def enroll(self, course_id: UUID, current_user: UserRead) -> EnrollmentRead:
        course = self._get_course_or_404(course_id)
        existing = self.enrollments.get_by_user_and_course(current_user.id, course.id)
        if existing is not None:
            return EnrollmentRead.model_validate(existing)
        enrollment = Enrollment(user_id=current_user.id, course_id=course.id)
        self.enrollments.create(enrollment)
        self.db.commit()
        self.db.refresh(enrollment)
        student_name = get_user_display_name(current_user)
        recipient_ids: set[UUID] = {course.author_id}
        for item in self.collaborators.list_by_course(course.id, status=CourseCollaboratorStatus.ACCEPTED):
            recipient_ids.add(item.user_id)
        for recipient_id in recipient_ids:
            if recipient_id == current_user.id:
                continue
            self.notifications.create_course_student_enrolled_notification(
                recipient_user_id=recipient_id,
                course_id=course.id,
                course_title=course.title,
                student_user_id=current_user.id,
                student_name=student_name,
            )
        return EnrollmentRead.model_validate(enrollment)

    def list_course_students(self, course_id: UUID, current_user: UserRead) -> list[CourseStudentEnrollmentRead]:
        course = self._get_course_for_management(course_id, current_user)
        enrollments = self.enrollments.list_by_course(course.id)
        return [
            self._to_course_student_enrollment_read(enrollment, course.id)
            for enrollment in enrollments
        ]

    def remove_student(self, course_id: UUID, student_id: UUID, current_user: UserRead) -> None:
        course = self._get_course_for_management(course_id, current_user)
        enrollment = self.enrollments.get_by_user_and_course(student_id, course.id)
        if enrollment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
        remover_name = get_user_display_name(current_user)
        self.notifications.create_course_student_removed_notification(
            recipient_user_id=student_id,
            course_id=course.id,
            course_title=course.title,
            remover_name=remover_name,
        )
        self.enrollments.delete(enrollment)
        self.db.commit()

    def has_course_access(self, course_id: UUID, current_user: UserRead) -> bool:
        course = self._get_course_or_404(course_id)
        if current_user.role == UserRole.ADMIN or course.author_id == current_user.id:
            return True
        if self.is_course_collaborator(course_id, current_user.id):
            return True
        return self.enrollments.get_by_user_and_course(current_user.id, course_id) is not None

    def is_course_collaborator(self, course_id: UUID, user_id: UUID) -> bool:
        invite = self.collaborators.get_by_course_and_user(course_id, user_id)
        return invite is not None and invite.status == CourseCollaboratorStatus.ACCEPTED

    def ensure_can_manage_course(self, course_id: UUID, current_user: UserRead) -> Course:
        return self._get_course_for_management(course_id, current_user)

    def ensure_can_delete_course_resources(self, course_id: UUID, current_user: UserRead) -> Course:
        return self._get_course_for_deletion(course_id, current_user)

    def _get_course_or_404(self, course_id: UUID) -> Course:
        course = self.courses.get_by_id(course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        return course

    def _get_course_for_management(self, course_id: UUID, current_user: UserRead) -> Course:
        course = self._get_course_or_404(course_id)
        if current_user.role == UserRole.ADMIN:
            return course
        if current_user.role != UserRole.TEACHER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        if course.author_id != current_user.id and not self.is_course_collaborator(course.id, current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return course

    def _get_course_for_deletion(self, course_id: UUID, current_user: UserRead) -> Course:
        course = self._get_course_or_404(course_id)
        if current_user.role == UserRole.ADMIN:
            return course
        if current_user.role != UserRole.TEACHER or course.author_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only course author can delete course")
        return course

    def _get_invite_for_current_user_or_404(self, invite_id: UUID, current_user: UserRead) -> CourseCollaborator:
        invite = self.db.get(CourseCollaborator, invite_id)
        if invite is None or invite.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
        if invite.status != CourseCollaboratorStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invite is not pending")
        return invite

    def _to_collaborator_read(self, collaborator: CourseCollaborator) -> CourseCollaboratorRead:
        return CourseCollaboratorRead(
            id=collaborator.id,
            course_id=collaborator.course_id,
            course_title=collaborator.course.title if collaborator.course is not None else None,
            user_id=collaborator.user_id,
            invited_by_user_id=collaborator.invited_by_user_id,
            status=collaborator.status,
            invite_message=collaborator.invite_message,
            created_at=collaborator.created_at,
            updated_at=collaborator.updated_at,
            accepted_at=collaborator.accepted_at,
            user_name=get_user_display_name(collaborator.user) if collaborator.user is not None else None,
            user_email=collaborator.user.email if collaborator.user is not None else None,
            inviter_name=get_user_display_name(collaborator.invited_by) if collaborator.invited_by is not None else None,
            inviter_email=collaborator.invited_by.email if collaborator.invited_by is not None else None,
        )

    def _to_course_student_enrollment_read(self, enrollment: Enrollment, course_id: UUID) -> CourseStudentEnrollmentRead:
        user = UserRead.model_validate(enrollment.user)
        analytics = self.progress.build_student_course_analytics(course_id, user)
        return CourseStudentEnrollmentRead(
            id=enrollment.id,
            course_id=enrollment.course_id,
            status=enrollment.status,
            enrolled_at=enrollment.enrolled_at,
            user=enrollment.user,
            progress=analytics["progress"],
            progress_status=analytics["progress_status"],
            last_activity_at=analytics["last_activity_at"],
            inactivity_days=analytics["inactivity_days"],
            pending_assignments_count=analytics["pending_assignments_count"],
            passed_quizzes_count=analytics["passed_quizzes_count"],
            failed_quizzes_count=analytics["failed_quizzes_count"],
            overdue_items_count=analytics["overdue_items_count"],
            upcoming_deadlines_count=analytics["upcoming_deadlines_count"],
            late_submissions_count=analytics["late_submissions_count"],
            average_assignment_score_percent=analytics["average_assignment_score_percent"],
            average_quiz_score_percent=analytics["average_quiz_score_percent"],
            recent_activity_count_7d=analytics["recent_activity_count_7d"],
            recent_completed_items_7d=analytics["recent_completed_items_7d"],
            pseudo_activity=analytics["pseudo_activity"],
            engagement_trend=analytics["engagement_trend"],
            risk_score=analytics["risk_score"],
            risk_level=analytics["risk_level"],
        )


def get_course_service(
    db: Session = Depends(get_db),
    media: MediaService = Depends(get_media_service),
    progress: ProgressService = Depends(get_progress_service),
    notifications: NotificationService = Depends(get_notification_service),
) -> CourseService:
    return CourseService(db, media, progress, notifications)
