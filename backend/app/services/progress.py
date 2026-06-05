from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.models.assignment import SubmissionStatus
from app.models.user import UserRole
from app.repositories.assignment import AssignmentSubmissionRepository
from app.repositories.content_progress import ContentProgressRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.module import ModuleRepository
from app.repositories.module_content import ModuleContentRepository
from app.repositories.quiz import QuizRepository
from app.schemas.progress import CourseProgressSummary, ModuleProgressSummary
from app.schemas.user import UserRead


class ProgressService:
    QUIZ_PASSING_RATIO = 0.6
    CONTENT_WEIGHT = 0.2
    ASSIGNMENT_WEIGHT = 0.5
    QUIZ_WEIGHT = 0.3
    UPCOMING_DEADLINE_WINDOW = timedelta(days=7)
    RECENT_ACTIVITY_WINDOW = timedelta(days=7)
    PSEUDO_ACTIVITY_GRACE_DAYS = 7
    PSEUDO_ACTIVITY_MIN_CONTENT_EVENTS_7D = 3
    RISK_ONBOARDING_GRACE_DAYS = 7
    RISK_ONBOARDING_MAX_SCORE = 45

    def __init__(self, db: Session) -> None:
        self.db = db
        self.modules = ModuleRepository(db)
        self.contents = ModuleContentRepository(db)
        self.content_progress = ContentProgressRepository(db)
        self.enrollments = EnrollmentRepository(db)
        self.quizzes = QuizRepository(db)
        self.assignment_submissions = AssignmentSubmissionRepository(db)

    def mark_content_viewed(self, content_id: UUID, current_user: UserRead) -> None:
        if current_user.role != UserRole.STUDENT:
            return
        self.content_progress.mark_viewed(current_user.id, content_id)
        self.db.commit()

    def build_course_progress(self, course_id: UUID, current_user: UserRead) -> CourseProgressSummary:
        if current_user.role != UserRole.STUDENT:
            return CourseProgressSummary()

        modules = [module for module in self.modules.list_by_course(course_id) if module.is_published]
        module_ids = [module.id for module in modules]
        viewed_content_ids = self.content_progress.list_viewed_content_ids(current_user.id, module_ids)

        module_summaries: list[ModuleProgressSummary] = []
        total_contents = 0
        viewed_contents = 0
        total_assignments = 0
        completed_assignments = 0
        total_quizzes = 0
        completed_quizzes = 0
        completed_modules = 0
        total_progress_units = 0.0
        earned_progress_units = 0.0

        for module in modules:
            contents = self.contents.list_by_module(module.id)
            assignments = [assignment for assignment in module.assignments if assignment.is_published]
            published_quiz = module.quiz if module.quiz is not None and module.quiz.is_published else None

            module_total_contents = len(contents)
            module_viewed_contents = sum(1 for content in contents if content.id in viewed_content_ids)
            module_total_assignments = len(assignments)
            module_completed_assignments = sum(
                1
                for assignment in assignments
                if (
                    submission := self.assignment_submissions.get_current_for_student(assignment.id, current_user.id)
                ) is not None
                and submission.status == SubmissionStatus.GRADED
            )
            module_total_quizzes = 1 if published_quiz is not None else 0
            module_completed_quizzes = (
                1
                if published_quiz is not None
                and self.quizzes.has_passing_attempt_for_user(
                    published_quiz.id,
                    current_user.id,
                    self.QUIZ_PASSING_RATIO,
                )
                else 0
            )

            module_completed_items = module_viewed_contents + module_completed_assignments + module_completed_quizzes
            module_total_items = module_total_contents + module_total_assignments + module_total_quizzes
            module_progress_ratio = self._calculate_weighted_progress_ratio(
                content_total=module_total_contents,
                content_completed=module_viewed_contents,
                assignment_total=module_total_assignments,
                assignment_completed=module_completed_assignments,
                quiz_total=module_total_quizzes,
                quiz_completed=module_completed_quizzes,
            )
            module_progress_percent = round(module_progress_ratio * 100) if module_total_items else 0

            if module_total_items and module_completed_items == module_total_items:
                completed_modules += 1

            total_contents += module_total_contents
            viewed_contents += module_viewed_contents
            total_assignments += module_total_assignments
            completed_assignments += module_completed_assignments
            total_quizzes += module_total_quizzes
            completed_quizzes += module_completed_quizzes
            total_progress_units += 1 if module_total_items else 0
            earned_progress_units += module_progress_ratio if module_total_items else 0

            module_summaries.append(
                ModuleProgressSummary(
                    module_id=str(module.id),
                    module_title=module.title,
                    progress_percent=module_progress_percent,
                    completed_items=module_completed_items,
                    total_items=module_total_items,
                )
            )

        total_items = total_contents + total_assignments + total_quizzes
        completed_items = viewed_contents + completed_assignments + completed_quizzes
        progress_percent = round((earned_progress_units / total_progress_units) * 100) if total_progress_units else 0

        return CourseProgressSummary(
            progress_percent=progress_percent,
            completed_items=completed_items,
            total_items=total_items,
            viewed_contents=viewed_contents,
            total_contents=total_contents,
            completed_assignments=completed_assignments,
            total_assignments=total_assignments,
            completed_quizzes=completed_quizzes,
            total_quizzes=total_quizzes,
            completed_modules=completed_modules,
            total_modules=len(modules),
            modules=module_summaries,
        )

    def build_student_course_analytics(self, course_id: UUID, current_user: UserRead) -> dict:
        progress = self.build_course_progress(course_id, current_user)
        modules = [module for module in self.modules.list_by_course(course_id) if module.is_published]
        module_ids = [module.id for module in modules]

        assignments = [assignment for module in modules for assignment in module.assignments if assignment.is_published]
        quizzes = [module.quiz for module in modules if module.quiz is not None and module.quiz.is_published]

        latest_activity = self.content_progress.latest_activity_at(current_user.id, module_ids)
        latest_activity = self._normalize_datetime(latest_activity)
        now = datetime.now(UTC)
        pending_assignments_count = 0
        passed_quizzes_count = 0
        failed_quizzes_count = 0
        overdue_items_count = 0
        upcoming_deadlines_count = 0
        late_submissions_count = 0
        graded_assignment_scores: list[int] = []
        attempted_quiz_scores: list[int] = []
        recent_content_activity_count_7d = 0
        recent_assessment_activity_count_7d = 0
        recent_activity_count_7d = 0
        recent_completed_items_7d = 0
        recent_window_start = now - self.RECENT_ACTIVITY_WINDOW
        enrollment = self.enrollments.get_by_user_and_course(current_user.id, course_id)
        enrollment_age_days = None
        if enrollment is not None:
            enrolled_at = self._normalize_datetime(enrollment.enrolled_at)
            if enrolled_at is not None:
                enrollment_age_days = max(0, int((now - enrolled_at).total_seconds() // 86400))

        recent_content_activity_count_7d += self.content_progress.recent_activity_count(
            current_user.id,
            module_ids,
            recent_window_start,
        )

        for assignment in assignments:
            submission = self.assignment_submissions.get_current_for_student(assignment.id, current_user.id)
            if submission is None:
                normalized_due_at = self._normalize_datetime(assignment.due_at)
                if normalized_due_at is not None:
                    if normalized_due_at < now:
                        overdue_items_count += 1
                    elif normalized_due_at <= now + self.UPCOMING_DEADLINE_WINDOW:
                        upcoming_deadlines_count += 1
                continue
            submission_updated_at = self._normalize_datetime(submission.updated_at)
            if latest_activity is None or (submission_updated_at is not None and submission_updated_at > latest_activity):
                latest_activity = submission_updated_at
            if submission_updated_at is not None and submission_updated_at >= recent_window_start:
                recent_assessment_activity_count_7d += 1
            if submission.status != SubmissionStatus.GRADED:
                pending_assignments_count += 1
            else:
                if submission.score is not None and assignment.max_score and assignment.max_score > 0:
                    graded_assignment_scores.append(round((submission.score / assignment.max_score) * 100))
                graded_at = self._normalize_datetime(submission.graded_at)
                if graded_at is not None and graded_at >= recent_window_start:
                    recent_completed_items_7d += 1
            normalized_due_at = self._normalize_datetime(assignment.due_at)
            submitted_at = self._normalize_datetime(submission.submitted_at)
            if normalized_due_at is not None and submitted_at is not None and submitted_at > normalized_due_at:
                late_submissions_count += 1

        for quiz in quizzes:
            attempts = self.quizzes.list_attempts_for_user(quiz.id, current_user.id)
            if not attempts:
                normalized_due_at = self._normalize_datetime(quiz.due_at)
                if normalized_due_at is not None:
                    if normalized_due_at < now:
                        overdue_items_count += 1
                    elif normalized_due_at <= now + self.UPCOMING_DEADLINE_WINDOW:
                        upcoming_deadlines_count += 1
                continue
            latest_attempt_at = self._normalize_datetime(attempts[0].created_at)
            if latest_activity is None or (latest_attempt_at is not None and latest_attempt_at > latest_activity):
                latest_activity = latest_attempt_at
            if latest_attempt_at is not None and latest_attempt_at >= recent_window_start:
                recent_assessment_activity_count_7d += 1
            best_score_percent = max(
                round((attempt.score / attempt.total_questions) * 100)
                for attempt in attempts
                if attempt.total_questions > 0
            )
            attempted_quiz_scores.append(best_score_percent)
            if self.quizzes.has_passing_attempt_for_user(quiz.id, current_user.id, self.QUIZ_PASSING_RATIO):
                latest_passing_attempt = next(
                    (
                        self._normalize_datetime(attempt.created_at)
                        for attempt in attempts
                        if attempt.total_questions > 0 and (attempt.score / attempt.total_questions) >= self.QUIZ_PASSING_RATIO
                    ),
                    None,
                )
                if latest_passing_attempt is not None and latest_passing_attempt >= recent_window_start:
                    recent_completed_items_7d += 1
            if self.quizzes.has_passing_attempt_for_user(quiz.id, current_user.id, self.QUIZ_PASSING_RATIO):
                passed_quizzes_count += 1
            else:
                failed_quizzes_count += 1

        recent_activity_count_7d = recent_content_activity_count_7d + recent_assessment_activity_count_7d
        pseudo_activity = (
            (enrollment_age_days is None or enrollment_age_days >= self.PSEUDO_ACTIVITY_GRACE_DAYS)
            and recent_content_activity_count_7d >= self.PSEUDO_ACTIVITY_MIN_CONTENT_EVENTS_7D
            and recent_assessment_activity_count_7d == 0
            and recent_completed_items_7d == 0
            and progress.progress_percent < 70
            and (pending_assignments_count > 0 or upcoming_deadlines_count > 0 or overdue_items_count > 0)
        )

        inactivity_days = None
        if latest_activity is not None:
            inactivity_days = max(0, int((now - latest_activity).total_seconds() // 86400))
        average_assignment_score_percent = (
            round(sum(graded_assignment_scores) / len(graded_assignment_scores)) if graded_assignment_scores else None
        )
        average_quiz_score_percent = (
            round(sum(attempted_quiz_scores) / len(attempted_quiz_scores)) if attempted_quiz_scores else None
        )
        engagement_trend = self._resolve_engagement_trend(
            recent_activity_count_7d=recent_activity_count_7d,
            recent_completed_items_7d=recent_completed_items_7d,
            inactivity_days=inactivity_days,
            pseudo_activity=pseudo_activity,
        )
        risk_score = self._calculate_risk_score(
            progress_percent=progress.progress_percent,
            inactivity_days=inactivity_days,
            failed_quizzes_count=failed_quizzes_count,
            overdue_items_count=overdue_items_count,
            late_submissions_count=late_submissions_count,
            pending_assignments_count=pending_assignments_count,
            upcoming_deadlines_count=upcoming_deadlines_count,
        )
        if (
            enrollment_age_days is not None
            and enrollment_age_days < self.RISK_ONBOARDING_GRACE_DAYS
            and recent_assessment_activity_count_7d == 0
            and recent_completed_items_7d == 0
            and progress.progress_percent < 25
        ):
            risk_score = min(risk_score, 30)
        elif enrollment_age_days is not None and enrollment_age_days < self.RISK_ONBOARDING_GRACE_DAYS:
            risk_score = min(risk_score, self.RISK_ONBOARDING_MAX_SCORE)
        risk_level = self._resolve_risk_level(risk_score)

        if progress.progress_percent >= 100:
            progress_status = "completed"
        elif latest_activity is not None or progress.progress_percent > 0:
            progress_status = "in_progress"
        else:
            progress_status = "not_started"

        return {
            "progress": progress,
            "progress_status": progress_status,
            "last_activity_at": latest_activity,
            "inactivity_days": inactivity_days,
            "pending_assignments_count": pending_assignments_count,
            "passed_quizzes_count": passed_quizzes_count,
            "failed_quizzes_count": failed_quizzes_count,
            "overdue_items_count": overdue_items_count,
            "upcoming_deadlines_count": upcoming_deadlines_count,
            "late_submissions_count": late_submissions_count,
            "average_assignment_score_percent": average_assignment_score_percent,
            "average_quiz_score_percent": average_quiz_score_percent,
            "recent_activity_count_7d": recent_activity_count_7d,
            "recent_completed_items_7d": recent_completed_items_7d,
            "pseudo_activity": pseudo_activity,
            "engagement_trend": engagement_trend,
            "risk_score": risk_score,
            "risk_level": risk_level,
        }

    def _calculate_weighted_progress_ratio(
        self,
        *,
        content_total: int,
        content_completed: int,
        assignment_total: int,
        assignment_completed: int,
        quiz_total: int,
        quiz_completed: int,
    ) -> float:
        groups = []
        if content_total > 0:
            groups.append((self.CONTENT_WEIGHT, content_completed / content_total))
        if assignment_total > 0:
            groups.append((self.ASSIGNMENT_WEIGHT, assignment_completed / assignment_total))
        if quiz_total > 0:
            groups.append((self.QUIZ_WEIGHT, quiz_completed / quiz_total))

        if not groups:
            return 0.0

        total_weight = sum(weight for weight, _ in groups)
        return sum((weight / total_weight) * ratio for weight, ratio in groups)

    def _calculate_risk_score(
        self,
        *,
        progress_percent: int,
        inactivity_days: int | None,
        failed_quizzes_count: int,
        overdue_items_count: int,
        late_submissions_count: int,
        pending_assignments_count: int,
        upcoming_deadlines_count: int,
    ) -> int:
        score = 0

        if progress_percent < 25:
            score += 35
        elif progress_percent < 50:
            score += 25
        elif progress_percent < 75:
            score += 10

        if inactivity_days is not None:
            if inactivity_days >= 14:
                score += 25
            elif inactivity_days >= 7:
                score += 15
            elif inactivity_days >= 3:
                score += 5

        score += min(failed_quizzes_count * 12, 24)
        score += min(overdue_items_count * 15, 30)
        score += min(late_submissions_count * 8, 16)

        if pending_assignments_count >= 2:
            score += 10
        elif pending_assignments_count == 1:
            score += 5

        if upcoming_deadlines_count >= 3:
            score += 8
        elif upcoming_deadlines_count >= 1:
            score += 4

        return min(score, 100)

    def _resolve_risk_level(self, risk_score: int) -> str:
        if risk_score >= 70:
            return "high"
        if risk_score >= 40:
            return "medium"
        return "low"

    def _resolve_engagement_trend(
        self,
        *,
        recent_activity_count_7d: int,
        recent_completed_items_7d: int,
        inactivity_days: int | None,
        pseudo_activity: bool,
    ) -> str:
        if pseudo_activity:
            return "stalled"
        if recent_completed_items_7d >= 2 or recent_activity_count_7d >= 3:
            return "growing"
        if inactivity_days is not None and inactivity_days >= 7:
            return "stalled"
        return "stable"

    def _normalize_datetime(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)



def get_progress_service(db: Session = Depends(get_db)) -> ProgressService:
    return ProgressService(db)
