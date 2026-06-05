from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.enrollment import Enrollment
from app.models.module import Module
from app.models.notification import Notification, NotificationType
from app.models.quiz import Quiz, QuizAttempt
from app.models.user import UserRole
from app.repositories.assignment import AssignmentSubmissionRepository
from app.repositories.course import CourseRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.notification import NotificationRepository
from app.repositories.quiz import QuizRepository
from app.schemas.notification import NotificationListResponse, NotificationRead
from app.schemas.user import UserRead


class NotificationService:
    DEADLINE_SOON_WINDOW = timedelta(hours=24)

    def __init__(self, db: Session) -> None:
        self.db = db
        self.notifications = NotificationRepository(db)
        self.courses = CourseRepository(db)
        self.enrollments = EnrollmentRepository(db)
        self.assignment_submissions = AssignmentSubmissionRepository(db)
        self.quizzes = QuizRepository(db)

    def list_my_notifications(self, current_user: UserRead, *, limit: int = 20) -> NotificationListResponse:
        self._sync_deadline_notifications(current_user)
        self._sync_performance_risk_notifications(current_user)
        items = self.notifications.list_for_user(current_user.id, limit=limit)
        unread_count = self.notifications.unread_count(current_user.id)
        return NotificationListResponse(
            items=[NotificationRead.model_validate(item) for item in items],
            unread_count=unread_count,
        )

    def mark_read(self, notification_id: UUID, current_user: UserRead) -> NotificationRead | None:
        notification = self.notifications.get_by_id_for_user(notification_id, current_user.id)
        if notification is None:
            return None
        self.notifications.mark_read(notification)
        self.db.commit()
        self.db.refresh(notification)
        return NotificationRead.model_validate(notification)

    def mark_all_read(self, current_user: UserRead) -> None:
        self.notifications.mark_all_read(current_user.id)
        self.db.commit()

    def delete_notification(self, notification_id: UUID, current_user: UserRead) -> bool:
        notification = self.notifications.get_by_id_for_user(notification_id, current_user.id)
        if notification is None:
            return False
        self.notifications.delete(notification)
        self.db.commit()
        return True

    def delete_read_notifications(self, current_user: UserRead) -> int:
        removed = self.notifications.delete_read_for_user(current_user.id)
        self.db.commit()
        return removed

    def create_comment_reply_notification(self, recipient_user_id: UUID, *, module_id: UUID, actor_name: str) -> None:
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.COMMENT_REPLY,
            title="Новый ответ в обсуждении",
            message=f"{actor_name} ответил(а) на ваш комментарий.",
            link_url=f"/modules/{module_id}",
        )

    def create_assignment_graded_notification(
        self,
        recipient_user_id: UUID,
        *,
        module_id: UUID,
        assignment_title: str,
        score: int | None,
    ) -> None:
        score_text = f" Оценка: {score}." if score is not None else ""
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.ASSIGNMENT_GRADED,
            title="Работа проверена",
            message=f"Преподаватель проверил задание «{assignment_title}».{score_text}",
            link_url=f"/modules/{module_id}",
        )

    def create_assignment_feedback_notification(
        self,
        recipient_user_id: UUID,
        *,
        module_id: UUID,
        assignment_title: str,
        feedback_markdown: str,
    ) -> None:
        feedback_preview = self._truncate_text(feedback_markdown, 140)
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.ASSIGNMENT_FEEDBACK,
            title="Новый комментарий к работе",
            message=f"Преподаватель оставил комментарий к заданию «{assignment_title}»: {feedback_preview}",
            link_url=f"/modules/{module_id}",
        )

    def create_assignment_submitted_notification(
        self,
        recipient_user_id: UUID,
        *,
        module_id: UUID,
        assignment_title: str,
        actor_name: str,
    ) -> None:
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.ASSIGNMENT_SUBMITTED,
            title="Новая сдача задания",
            message=f"{actor_name} отправил(а) ответ на задание «{assignment_title}».",
            link_url=f"/modules/{module_id}",
        )

    def create_assignment_published_notifications(
        self,
        course_id: UUID,
        *,
        module_id: UUID,
        assignment_id: UUID,
        assignment_title: str,
    ) -> None:
        self._broadcast_to_course_students(
            course_id,
            type=NotificationType.ASSIGNMENT_PUBLISHED,
            title="Новое задание в курсе",
            message=f"В курсе появилось новое задание «{assignment_title}».",
            link_url=f"/modules/{module_id}",
            dedupe_key_factory=lambda user_id: f"assignment:published:{assignment_id}:{user_id}",
        )

    def create_quiz_published_notifications(
        self,
        course_id: UUID,
        *,
        module_id: UUID,
        quiz_id: UUID,
        quiz_title: str,
    ) -> None:
        self._broadcast_to_course_students(
            course_id,
            type=NotificationType.QUIZ_PUBLISHED,
            title="Новый тест в курсе",
            message=f"В курсе опубликован тест «{quiz_title}».",
            link_url=f"/modules/{module_id}",
            dedupe_key_factory=lambda user_id: f"quiz:published:{quiz_id}:{user_id}",
        )

    def create_deadline_changed_notifications(
        self,
        course_id: UUID,
        *,
        module_id: UUID,
        entity_kind: str,
        entity_id: UUID,
        item_title: str,
        previous_due_at: datetime | None,
        due_at: datetime | None,
    ) -> None:
        if previous_due_at == due_at:
            return

        previous_label = self._format_due_label(previous_due_at)
        current_label = self._format_due_label(due_at)
        if previous_due_at is None and due_at is not None:
            message = f"Для {entity_kind} «{item_title}» установлен дедлайн: {current_label}."
        elif previous_due_at is not None and due_at is None:
            message = f"Для {entity_kind} «{item_title}» дедлайн снят."
        else:
            message = f"Для {entity_kind} «{item_title}» дедлайн изменён: было {previous_label}, стало {current_label}."

        due_key = due_at.isoformat() if due_at is not None else "none"
        self._broadcast_to_course_students(
            course_id,
            type=NotificationType.DEADLINE_CHANGED,
            title="Изменение дедлайна",
            message=message,
            link_url=f"/modules/{module_id}",
            dedupe_key_factory=lambda user_id: f"deadline:changed:{entity_kind}:{entity_id}:{due_key}:{user_id}",
            data_json={"entity_type": entity_kind, "entity_id": str(entity_id), "due_at": due_key},
        )

    def create_teacher_announcement_notifications(
        self,
        course_id: UUID,
        *,
        module_id: UUID,
        comment_id: UUID,
        actor_name: str,
        content: str,
    ) -> None:
        preview = self._truncate_text(content, 160)
        self._broadcast_to_course_students(
            course_id,
            type=NotificationType.TEACHER_ANNOUNCEMENT,
            title="Новое объявление от преподавателя",
            message=f"{actor_name}: {preview}",
            link_url=f"/modules/{module_id}",
            dedupe_key_factory=lambda user_id: f"teacher:announcement:{comment_id}:{user_id}",
        )

    def create_chat_message_notification(
        self,
        recipient_user_id: UUID,
        *,
        sender_user_id: UUID,
        sender_name: str,
        message_text: str,
    ) -> None:
        preview = self._truncate_text(message_text, 140)
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.CHAT_MESSAGE,
            title="Новое сообщение",
            message=f"{sender_name}: {preview}",
            link_url=f"/chat?partner={sender_user_id}",
            data_json={"sender_user_id": str(sender_user_id)},
        )

    def create_course_student_enrolled_notification(
        self,
        recipient_user_id: UUID,
        *,
        course_id: UUID,
        course_title: str,
        student_user_id: UUID,
        student_name: str,
    ) -> None:
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.TEACHER_ANNOUNCEMENT,
            title="Новая запись на курс",
            message=f"{student_name} записался(ась) на курс «{course_title}».",
            link_url=f"/courses/{course_id}/progress",
            data_json={"course_id": str(course_id), "student_user_id": str(student_user_id)},
        )

    def create_course_student_removed_notification(
        self,
        recipient_user_id: UUID,
        *,
        course_id: UUID,
        course_title: str,
        remover_name: str,
    ) -> None:
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.TEACHER_ANNOUNCEMENT,
            title="Вы отчислены с курса",
            message=f"{remover_name} удалил(а) вас с курса «{course_title}».",
            link_url=f"/courses/{course_id}",
            data_json={"course_id": str(course_id)},
        )

    def create_course_collaboration_invite_notification(
        self,
        recipient_user_id: UUID,
        *,
        inviter_user_id: UUID,
        inviter_name: str,
        course_id: UUID,
        course_title: str,
        message_text: str | None = None,
    ) -> None:
        suffix = f" Сообщение: {self._truncate_text(message_text, 140)}" if message_text else ""
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.TEACHER_ANNOUNCEMENT,
            title="Приглашение в соавторы",
            message=f"{inviter_name} приглашает вас в соавторы курса «{course_title}».{suffix}",
            link_url="/my-courses",
            data_json={"inviter_user_id": str(inviter_user_id), "course_id": str(course_id)},
        )

    def create_course_collaborator_removed_notification(
        self,
        recipient_user_id: UUID,
        *,
        course_id: UUID,
        course_title: str,
        remover_name: str,
    ) -> None:
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.TEACHER_ANNOUNCEMENT,
            title="Доступ соавтора отозван",
            message=f"{remover_name} удалил вас из соавторов курса «{course_title}».",
            link_url="/my-courses",
            data_json={"course_id": str(course_id)},
        )

    def create_admin_comment_hidden_notification(self, recipient_user_id: UUID, *, module_id: UUID) -> None:
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.TEACHER_ANNOUNCEMENT,
            title="Комментарий скрыт модератором",
            message="Администратор скрыл ваш комментарий после проверки жалобы.",
            link_url=f"/modules/{module_id}",
        )

    def create_admin_comment_restored_notification(self, recipient_user_id: UUID, *, module_id: UUID) -> None:
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.TEACHER_ANNOUNCEMENT,
            title="Комментарий восстановлен",
            message="Администратор восстановил ваш комментарий.",
            link_url=f"/modules/{module_id}",
        )

    def create_admin_course_hidden_notification(
        self,
        recipient_user_id: UUID,
        *,
        course_id: UUID,
        course_title: str,
    ) -> None:
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.TEACHER_ANNOUNCEMENT,
            title="Курс скрыт модератором",
            message=f"Администратор временно скрыл курс «{course_title}».",
            link_url=f"/courses/{course_id}",
        )

    def create_admin_course_restored_notification(
        self,
        recipient_user_id: UUID,
        *,
        course_id: UUID,
        course_title: str,
    ) -> None:
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.TEACHER_ANNOUNCEMENT,
            title="Курс восстановлен",
            message=f"Администратор снова опубликовал курс «{course_title}».",
            link_url=f"/courses/{course_id}",
        )

    def create_admin_report_reviewed_notification(
        self,
        recipient_user_id: UUID,
        *,
        report_id: UUID,
        status: str,
        resolution_note: str | None = None,
    ) -> None:
        status_map = {
            "open": "Открыт",
            "in_review": "На проверке",
            "resolved": "Решен",
            "rejected": "Отклонен",
        }
        status_label = status_map.get(status, status)
        note = f" Комментарий: {self._truncate_text(resolution_note, 160)}" if resolution_note else ""
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.TEACHER_ANNOUNCEMENT,
            title="Ваша жалоба рассмотрена",
            message=f"Администратор обновил статус жалобы: {status_label}.{note}",
            link_url="/dashboard",
            data_json={"report_id": str(report_id), "status": status},
        )

    def create_admin_role_changed_notification(self, recipient_user_id: UUID, *, new_role: str) -> None:
        label = {"admin": "администратор", "teacher": "преподаватель", "student": "студент"}.get(new_role, new_role)
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.TEACHER_ANNOUNCEMENT,
            title="Роль аккаунта изменена",
            message=f"Администратор назначил вам роль «{label}».",
            link_url="/profile",
        )

    def create_admin_account_blocked_notification(
        self,
        recipient_user_id: UUID,
        *,
        blocked_until: datetime | None,
        reason: str | None,
    ) -> None:
        if blocked_until is None:
            period = "бессрочно"
        else:
            period = blocked_until.astimezone(UTC).strftime("%d.%m.%Y %H:%M UTC")
        reason_text = f" Причина: {reason}." if reason else ""
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.TEACHER_ANNOUNCEMENT,
            title="Доступ к аккаунту ограничен",
            message=f"Администратор ограничил доступ к вашему аккаунту ({period}).{reason_text}",
            link_url="/auth",
        )

    def create_admin_account_unblocked_notification(self, recipient_user_id: UUID) -> None:
        self._create_notification(
            user_id=recipient_user_id,
            type=NotificationType.TEACHER_ANNOUNCEMENT,
            title="Доступ к аккаунту восстановлен",
            message="Администратор снял ограничение с вашего аккаунта.",
            link_url="/auth",
        )

    def _create_notification(
        self,
        *,
        user_id: UUID,
        type: NotificationType,
        title: str,
        message: str,
        link_url: str | None,
        dedupe_key: str | None = None,
        data_json: dict | None = None,
    ) -> None:
        if dedupe_key and self.notifications.get_by_dedupe_key(dedupe_key) is not None:
            return
        self.notifications.create(
            Notification(
                user_id=user_id,
                type=type,
                title=title,
                message=message,
                link_url=link_url,
                dedupe_key=dedupe_key,
                data_json=data_json,
            )
        )
        self.db.commit()

    def _broadcast_to_course_students(
        self,
        course_id: UUID,
        *,
        type: NotificationType,
        title: str,
        message: str,
        link_url: str | None,
        dedupe_key_factory,
        data_json: dict | None = None,
    ) -> None:
        for enrollment in self.enrollments.list_by_course(course_id):
            self._create_notification(
                user_id=enrollment.user_id,
                type=type,
                title=title,
                message=message,
                link_url=link_url,
                dedupe_key=dedupe_key_factory(enrollment.user_id),
                data_json=data_json,
            )

    def _sync_deadline_notifications(self, current_user: UserRead) -> None:
        if current_user.role != UserRole.STUDENT:
            return

        now = datetime.now(UTC)
        soon_until = now + self.DEADLINE_SOON_WINDOW

        assignments_stmt = (
            select(Assignment)
            .join(Module, Assignment.module_id == Module.id)
            .join(Enrollment, Enrollment.course_id == Module.course_id)
            .where(
                Enrollment.user_id == current_user.id,
                Module.is_published.is_(True),
                Assignment.is_published.is_(True),
                Assignment.due_at.is_not(None),
            )
        )
        assignments = list(self.db.scalars(assignments_stmt))
        for assignment in assignments:
            current_submission = self.assignment_submissions.get_current_for_student(assignment.id, current_user.id)
            if current_submission is not None:
                continue
            due_at = self._normalize_datetime(assignment.due_at)
            if due_at is None:
                continue
            iso_due = due_at.isoformat()
            if now <= due_at <= soon_until:
                self._create_notification(
                    user_id=current_user.id,
                    type=NotificationType.DEADLINE_SOON,
                    title="Скоро дедлайн по заданию",
                    message=f"У задания «{assignment.title}» скоро истекает срок сдачи.",
                    link_url=f"/modules/{assignment.module_id}",
                    dedupe_key=f"assignment:soon:{assignment.id}:{iso_due}",
                    data_json={"entity_type": "assignment", "entity_id": str(assignment.id), "due_at": iso_due},
                )
            if due_at < now:
                self._create_notification(
                    user_id=current_user.id,
                    type=NotificationType.DEADLINE_OVERDUE,
                    title="Дедлайн задания просрочен",
                    message=f"Срок сдачи задания «{assignment.title}» уже прошел.",
                    link_url=f"/modules/{assignment.module_id}",
                    dedupe_key=f"assignment:overdue:{assignment.id}:{iso_due}",
                    data_json={"entity_type": "assignment", "entity_id": str(assignment.id), "due_at": iso_due},
                )

        quizzes_stmt = (
            select(Quiz)
            .join(Module, Quiz.module_id == Module.id)
            .join(Enrollment, Enrollment.course_id == Module.course_id)
            .where(
                Enrollment.user_id == current_user.id,
                Module.is_published.is_(True),
                Quiz.is_published.is_(True),
                Quiz.due_at.is_not(None),
            )
        )
        quizzes = list(self.db.scalars(quizzes_stmt))
        for quiz in quizzes:
            if self.quizzes.has_attempt_for_user(quiz.id, current_user.id):
                continue
            due_at = self._normalize_datetime(quiz.due_at)
            if due_at is None:
                continue
            iso_due = due_at.isoformat()
            if now <= due_at <= soon_until:
                self._create_notification(
                    user_id=current_user.id,
                    type=NotificationType.DEADLINE_SOON,
                    title="Скоро дедлайн по тесту",
                    message=f"У теста «{quiz.title}» скоро истекает срок прохождения.",
                    link_url=f"/modules/{quiz.module_id}",
                    dedupe_key=f"quiz:soon:{quiz.id}:{iso_due}",
                    data_json={"entity_type": "quiz", "entity_id": str(quiz.id), "due_at": iso_due},
                )
            if due_at < now:
                self._create_notification(
                    user_id=current_user.id,
                    type=NotificationType.DEADLINE_OVERDUE,
                    title="Дедлайн теста просрочен",
                    message=f"Срок прохождения теста «{quiz.title}» уже прошел.",
                    link_url=f"/modules/{quiz.module_id}",
                    dedupe_key=f"quiz:overdue:{quiz.id}:{iso_due}",
                    data_json={"entity_type": "quiz", "entity_id": str(quiz.id), "due_at": iso_due},
                )

    def _sync_performance_risk_notifications(self, current_user: UserRead) -> None:
        if current_user.role != UserRole.STUDENT:
            return

        from app.services.progress import ProgressService

        progress_service = ProgressService(self.db)
        for enrollment in self.enrollments.list_by_user(current_user.id):
            course = self.courses.get_by_id(enrollment.course_id)
            if course is None or not course.is_published:
                continue

            analytics = progress_service.build_student_course_analytics(course.id, current_user)
            progress = analytics["progress"]
            failed_quizzes = analytics["failed_quizzes_count"]
            pending_assignments = analytics["pending_assignments_count"]
            overdue_items = analytics["overdue_items_count"]
            upcoming_deadlines = analytics["upcoming_deadlines_count"]
            risk_score = analytics["risk_score"]
            risk_level = analytics["risk_level"]

            if risk_level == "low":
                continue

            message_parts = [
                f"Прогресс по курсу «{course.title}» сейчас {progress.progress_percent}%.",
                f"Уровень риска: {self._risk_level_label(risk_level)} ({risk_score}/100).",
            ]
            if pending_assignments:
                message_parts.append(f"Непроверенных заданий: {pending_assignments}.")
            if failed_quizzes:
                message_parts.append(f"Тестов с непроходным результатом: {failed_quizzes}.")
            if overdue_items:
                message_parts.append(f"Просроченных активностей: {overdue_items}.")
            if upcoming_deadlines:
                message_parts.append(f"Ближайших дедлайнов на 7 дней: {upcoming_deadlines}.")

            self._create_notification(
                user_id=current_user.id,
                type=NotificationType.PERFORMANCE_RISK,
                title="Риск по успеваемости",
                message=" ".join(message_parts),
                link_url=f"/courses/{course.id}",
                dedupe_key=(
                    f"performance:risk:{course.id}:{risk_level}:{risk_score}:{pending_assignments}:{failed_quizzes}:{overdue_items}"
                ),
                data_json={
                    "course_id": str(course.id),
                    "progress_percent": progress.progress_percent,
                    "pending_assignments_count": pending_assignments,
                    "failed_quizzes_count": failed_quizzes,
                    "overdue_items_count": overdue_items,
                    "upcoming_deadlines_count": upcoming_deadlines,
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                },
            )

    def _normalize_datetime(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _format_due_label(self, value: datetime | None) -> str:
        if value is None:
            return "без срока"
        normalized = self._normalize_datetime(value)
        assert normalized is not None
        return normalized.strftime("%d.%m.%Y %H:%M UTC")

    def _truncate_text(self, value: str, limit: int) -> str:
        compact = " ".join(value.split())
        if len(compact) <= limit:
            return compact
        return compact[: limit - 1].rstrip() + "…"

    def _risk_level_label(self, value: str) -> str:
        if value == "high":
            return "высокий"
        if value == "medium":
            return "средний"
        return "низкий"


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(db)
