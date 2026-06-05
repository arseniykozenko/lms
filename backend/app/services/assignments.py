from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.lib.user_name import get_user_display_name
from app.models.assignment import (
    Assignment,
    AssignmentAttachment,
    AssignmentSubmission,
    AssignmentSubmissionAttachment,
    SubmissionStatus,
)
from app.models.module import Module
from app.models.user import UserRole
from app.repositories.assignment import AssignmentRepository, AssignmentSubmissionRepository
from app.repositories.module import ModuleRepository
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentRead,
    AssignmentSubmissionCreate,
    AssignmentSubmissionGrade,
    AssignmentSubmissionRead,
    AssignmentUpdate,
)
from app.schemas.user import UserRead
from app.services.courses import CourseService, get_course_service
from app.services.media import MediaService, get_media_service
from app.services.notifications import NotificationService, get_notification_service


class AssignmentService:
    def __init__(self, db: Session, courses: CourseService, media: MediaService, notifications: NotificationService) -> None:
        self.db = db
        self.courses = courses
        self.media = media
        self.notifications = notifications
        self.modules = ModuleRepository(db)
        self.assignments = AssignmentRepository(db)
        self.submissions = AssignmentSubmissionRepository(db)

    def list_module_assignments(self, module_id: UUID, current_user: UserRead) -> list[AssignmentRead]:
        module = self._get_module_or_404(module_id)
        self._ensure_module_view_access(module, current_user)
        items = self.assignments.list_by_module(module.id)
        visible = [
            item
            for item in items
            if item.is_published
            or current_user.role == UserRole.ADMIN
            or item.module.course.author_id == current_user.id
            or self.courses.is_course_collaborator(item.module.course_id, current_user.id)
        ]
        return [self._to_assignment_read(item) for item in visible]

    def create_assignment(self, module_id: UUID, payload: AssignmentCreate, current_user: UserRead) -> AssignmentRead:
        module = self._get_module_for_management(module_id, current_user)
        assignment = Assignment(
            module_id=module.id,
            title=payload.title.strip(),
            instructions_markdown=payload.instructions_markdown.strip(),
            max_score=payload.max_score,
            due_at=self._normalize_datetime(payload.due_at),
            is_published=payload.is_published,
        )
        self.assignments.create(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        if assignment.is_published:
            self.notifications.create_assignment_published_notifications(
                module.course_id,
                module_id=module.id,
                assignment_id=assignment.id,
                assignment_title=assignment.title,
            )
        return self._to_assignment_read(assignment)

    def get_assignment(self, assignment_id: UUID, current_user: UserRead) -> AssignmentRead:
        assignment = self._get_assignment_or_404(assignment_id)
        self._ensure_assignment_view_access(assignment, current_user)
        return self._to_assignment_read(assignment)

    def update_assignment(self, assignment_id: UUID, payload: AssignmentUpdate, current_user: UserRead) -> AssignmentRead:
        assignment = self._get_assignment_for_management(assignment_id, current_user)
        previous_due_at = assignment.due_at
        was_published = assignment.is_published
        if "title" in payload.model_fields_set and payload.title is not None:
            assignment.title = payload.title.strip()
        if "instructions_markdown" in payload.model_fields_set and payload.instructions_markdown is not None:
            assignment.instructions_markdown = payload.instructions_markdown.strip()
        if "max_score" in payload.model_fields_set:
            assignment.max_score = payload.max_score
        if "due_at" in payload.model_fields_set:
            assignment.due_at = self._normalize_datetime(payload.due_at)
        if "is_published" in payload.model_fields_set and payload.is_published is not None:
            assignment.is_published = payload.is_published
        self.db.commit()
        self.db.refresh(assignment)
        if assignment.is_published and not was_published:
            self.notifications.create_assignment_published_notifications(
                assignment.module.course_id,
                module_id=assignment.module_id,
                assignment_id=assignment.id,
                assignment_title=assignment.title,
            )
        if assignment.is_published and previous_due_at != assignment.due_at:
            self.notifications.create_deadline_changed_notifications(
                assignment.module.course_id,
                module_id=assignment.module_id,
                entity_kind="задания",
                entity_id=assignment.id,
                item_title=assignment.title,
                previous_due_at=previous_due_at,
                due_at=assignment.due_at,
            )
        return self._to_assignment_read(assignment)

    def delete_assignment(self, assignment_id: UUID, current_user: UserRead) -> None:
        assignment = self._get_assignment_for_management(assignment_id, current_user)
        self.courses.ensure_can_delete_course_resources(assignment.module.course_id, current_user)
        self.assignments.delete(assignment)
        self.db.commit()

    def upload_assignment_attachment(
        self,
        assignment_id: UUID,
        uploads: list[UploadFile],
        current_user: UserRead,
    ) -> AssignmentRead:
        assignment = self._get_assignment_for_management(assignment_id, current_user)
        if not uploads:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Attach at least one file")
        self._replace_assignment_attachments(assignment, uploads)
        self.db.commit()
        self.db.refresh(assignment)
        return self._to_assignment_read(assignment)

    def clear_assignment_attachments(self, assignment_id: UUID, current_user: UserRead) -> AssignmentRead:
        assignment = self._get_assignment_for_management(assignment_id, current_user)
        assignment.attachments.clear()
        assignment.attachment_url = None
        assignment.attachment_name = None
        self.db.commit()
        self.db.refresh(assignment)
        return self._to_assignment_read(assignment)

    def list_my_submissions(self, assignment_id: UUID, current_user: UserRead) -> list[AssignmentSubmissionRead]:
        assignment = self._get_assignment_or_404(assignment_id)
        self._ensure_assignment_view_access(assignment, current_user)
        current_submission = self.submissions.get_current_for_student(assignment.id, current_user.id)
        if current_submission is None:
            return []
        return [self._to_submission_read(current_submission)]

    def create_submission(
        self,
        assignment_id: UUID,
        payload: AssignmentSubmissionCreate,
        uploads: list[UploadFile] | None,
        current_user: UserRead,
    ) -> AssignmentSubmissionRead:
        assignment = self._get_assignment_or_404(assignment_id)
        self._ensure_assignment_submission_access(assignment, current_user)
        answer_markdown = (payload.answer_markdown or "").strip() or None
        uploads = uploads or []
        if answer_markdown is None and not uploads:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Submission must contain markdown text or at least one attachment",
            )
        existing_submission = self.submissions.get_current_for_student(assignment.id, current_user.id)
        if existing_submission is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a submitted answer for this assignment. Edit or delete it before sending a new one.",
            )

        submission = AssignmentSubmission(
            assignment_id=assignment.id,
            student_id=current_user.id,
            attempt_number=self.submissions.next_attempt_number(assignment.id, current_user.id),
            answer_markdown=answer_markdown,
            status=SubmissionStatus.SUBMITTED,
        )
        self.submissions.create(submission)
        if uploads:
            self._replace_submission_attachments(submission, uploads)
        self.db.commit()
        self.db.refresh(submission)
        author = assignment.module.course.author
        if author is not None and author.id != current_user.id:
            self.notifications.create_assignment_submitted_notification(
                author.id,
                module_id=assignment.module_id,
                assignment_title=assignment.title,
                actor_name=get_user_display_name(current_user),
            )
        return self._to_submission_read(submission)

    def update_submission(
        self,
        submission_id: UUID,
        payload: AssignmentSubmissionCreate,
        uploads: list[UploadFile] | None,
        current_user: UserRead,
    ) -> AssignmentSubmissionRead:
        submission = self._get_submission_for_owner(submission_id, current_user)
        answer_markdown = (payload.answer_markdown or "").strip() or None
        uploads = uploads or []

        if answer_markdown is None and not uploads and not submission.attachments:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Submission must contain markdown text or at least one attachment",
            )

        submission.answer_markdown = answer_markdown
        submission.status = SubmissionStatus.SUBMITTED
        submission.score = None
        submission.feedback_markdown = None
        submission.graded_at = None
        submission.submitted_at = datetime.now(UTC)
        if uploads:
            self._replace_submission_attachments(submission, uploads)
        self.db.commit()
        self.db.refresh(submission)
        author = submission.assignment.module.course.author
        if author is not None and author.id != current_user.id:
            self.notifications.create_assignment_submitted_notification(
                author.id,
                module_id=submission.assignment.module_id,
                assignment_title=submission.assignment.title,
                actor_name=get_user_display_name(current_user),
            )
        return self._to_submission_read(submission)

    def delete_submission(self, submission_id: UUID, current_user: UserRead) -> None:
        submission = self._get_submission_for_owner(submission_id, current_user)
        self.submissions.delete(submission)
        self.db.commit()

    def list_assignment_submissions(self, assignment_id: UUID, current_user: UserRead) -> list[AssignmentSubmissionRead]:
        assignment = self._get_assignment_for_management(assignment_id, current_user)
        submissions = self.submissions.list_for_assignment(assignment.id)
        return [self._to_submission_read(item) for item in submissions]

    def grade_submission(
        self,
        submission_id: UUID,
        payload: AssignmentSubmissionGrade,
        current_user: UserRead,
    ) -> AssignmentSubmissionRead:
        submission = self._get_submission_for_management(submission_id, current_user)
        submission.score = payload.score
        submission.feedback_markdown = (payload.feedback_markdown or "").strip() or None
        submission.status = SubmissionStatus.GRADED
        submission.graded_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(submission)
        if submission.student_id != current_user.id:
            feedback = submission.feedback_markdown
            if feedback:
                self.notifications.create_assignment_feedback_notification(
                    submission.student_id,
                    module_id=submission.assignment.module_id,
                    assignment_title=submission.assignment.title,
                    feedback_markdown=feedback,
                )
            else:
                self.notifications.create_assignment_graded_notification(
                    submission.student_id,
                    module_id=submission.assignment.module_id,
                    assignment_title=submission.assignment.title,
                    score=submission.score,
                )
        return self._to_submission_read(submission)

    def _to_assignment_read(self, assignment: Assignment) -> AssignmentRead:
        return AssignmentRead(
            id=assignment.id,
            module_id=assignment.module_id,
            title=assignment.title,
            instructions_markdown=assignment.instructions_markdown,
            attachment_url=assignment.attachment_url,
            attachment_name=assignment.attachment_name,
            max_score=assignment.max_score,
            due_at=assignment.due_at,
            is_published=assignment.is_published,
            has_submissions=bool(assignment.submissions),
            attachments=assignment.attachments,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
        )

    def _to_submission_read(self, submission: AssignmentSubmission) -> AssignmentSubmissionRead:
        return AssignmentSubmissionRead(
            id=submission.id,
            assignment_id=submission.assignment_id,
            student_id=submission.student_id,
            attempt_number=submission.attempt_number,
            answer_markdown=submission.answer_markdown,
            attachment_url=submission.attachment_url,
            attachment_name=submission.attachment_name,
            status=submission.status,
            score=submission.score,
            feedback_markdown=submission.feedback_markdown,
            submitted_at=submission.submitted_at,
            graded_at=submission.graded_at,
            is_late=bool(
                submission.assignment.due_at is not None and submission.submitted_at > submission.assignment.due_at
            ),
            created_at=submission.created_at,
            updated_at=submission.updated_at,
            student=submission.student,
            attachments=submission.attachments,
        )

    def _replace_assignment_attachments(self, assignment: Assignment, uploads: list[UploadFile]) -> None:
        assignment.attachments.clear()
        first_attachment = None
        for upload in uploads:
            asset = self.media.upload_module_asset(str(assignment.module_id), upload, requested_kind="assignment")
            attachment = AssignmentAttachment(
                file_url=asset["url"],
                file_name=upload.filename or "assignment-attachment",
            )
            assignment.attachments.append(attachment)
            if first_attachment is None:
                first_attachment = attachment

        assignment.attachment_url = first_attachment.file_url if first_attachment else None
        assignment.attachment_name = first_attachment.file_name if first_attachment else None

    def _replace_submission_attachments(self, submission: AssignmentSubmission, uploads: list[UploadFile]) -> None:
        submission.attachments.clear()
        first_attachment = None
        for upload in uploads:
            asset = self.media.upload_module_asset(str(submission.assignment.module_id), upload, requested_kind="submission")
            attachment = AssignmentSubmissionAttachment(
                file_url=asset["url"],
                file_name=upload.filename or "submission-attachment",
            )
            submission.attachments.append(attachment)
            if first_attachment is None:
                first_attachment = attachment

        submission.attachment_url = first_attachment.file_url if first_attachment else None
        submission.attachment_name = first_attachment.file_name if first_attachment else None

    def _get_module_or_404(self, module_id: UUID) -> Module:
        module = self.modules.get_by_id(module_id)
        if module is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
        return module

    def _get_assignment_or_404(self, assignment_id: UUID) -> Assignment:
        assignment = self.assignments.get_by_id(assignment_id)
        if assignment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
        return assignment

    def _get_module_for_management(self, module_id: UUID, current_user: UserRead) -> Module:
        module = self._get_module_or_404(module_id)
        self.courses.ensure_can_manage_course(module.course_id, current_user)
        return module

    def _get_assignment_for_management(self, assignment_id: UUID, current_user: UserRead) -> Assignment:
        assignment = self._get_assignment_or_404(assignment_id)
        self._get_module_for_management(assignment.module_id, current_user)
        return assignment

    def _get_submission_for_management(self, submission_id: UUID, current_user: UserRead) -> AssignmentSubmission:
        submission = self.submissions.get_by_id(submission_id)
        if submission is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
        self._get_module_for_management(submission.assignment.module_id, current_user)
        return submission

    def _get_submission_for_owner(self, submission_id: UUID, current_user: UserRead) -> AssignmentSubmission:
        submission = self.submissions.get_by_id(submission_id)
        if submission is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
        self._ensure_assignment_submission_access(submission.assignment, current_user)
        if submission.student_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can manage only your own submission")
        return submission

    def _ensure_module_view_access(self, module: Module, current_user: UserRead) -> None:
        if not self.courses.has_course_access(module.course_id, current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not enrolled in this course")
        if (
            not module.is_published
            and current_user.role != UserRole.ADMIN
            and module.course.author_id != current_user.id
            and not self.courses.is_course_collaborator(module.course_id, current_user.id)
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Module is not published")

    def _ensure_assignment_view_access(self, assignment: Assignment, current_user: UserRead) -> None:
        self._ensure_module_view_access(assignment.module, current_user)
        if (
            not assignment.is_published
            and current_user.role != UserRole.ADMIN
            and assignment.module.course.author_id != current_user.id
            and not self.courses.is_course_collaborator(assignment.module.course_id, current_user.id)
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Assignment is not published")

    def _ensure_assignment_submission_access(self, assignment: Assignment, current_user: UserRead) -> None:
        self._ensure_assignment_view_access(assignment, current_user)
        if current_user.role == UserRole.ADMIN:
            return
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can submit assignments")

    def _normalize_datetime(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


def get_assignment_service(
    db: Session = Depends(get_db),
    courses: CourseService = Depends(get_course_service),
    media: MediaService = Depends(get_media_service),
    notifications: NotificationService = Depends(get_notification_service),
) -> AssignmentService:
    return AssignmentService(db, courses, media, notifications)
