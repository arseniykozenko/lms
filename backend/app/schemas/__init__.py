"""Schema package."""
from app.schemas.admin_audit_log import AdminAuditLogRead
from app.schemas.ai_insights import CourseAiInsightsResponse, StudentAiInsightsResponse
from app.schemas.analytics import AnalyticsOverview, DailyEnrollmentPoint
from app.schemas.chat import ChatConversationRead, ChatMessageCreate, ChatMessageRead
from app.schemas.comment import CommentCreate, CommentRead
from app.schemas.course import (
    CourseCollaboratorInviteCreate,
    CourseCollaboratorRead,
    CourseCreate,
    CourseRead,
    CourseUpdate,
    EnrolledCourseRead,
)
from app.schemas.enrollment import EnrollmentRead
from app.schemas.module import ModuleCreate, ModuleRead, ModuleUpdate
from app.schemas.notification import NotificationListResponse, NotificationRead
from app.schemas.progress import CourseProgressSummary, ModuleProgressSummary
from app.schemas.quiz import (
    QuestionCreate,
    QuestionRead,
    QuizAttemptRead,
    QuizCreate,
    QuizRead,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from app.schemas.user import UserCreate, UserRead, UserUpdate

__all__ = [
    "AdminAuditLogRead",
    "CourseAiInsightsResponse",
    "StudentAiInsightsResponse",
    "AnalyticsOverview",
    "ChatConversationRead",
    "ChatMessageCreate",
    "ChatMessageRead",
    "CommentCreate",
    "CommentRead",
    "CourseCreate",
    "CourseCollaboratorInviteCreate",
    "CourseCollaboratorRead",
    "CourseRead",
    "CourseUpdate",
    "CourseProgressSummary",
    "DailyEnrollmentPoint",
    "EnrollmentRead",
    "EnrolledCourseRead",
    "ModuleCreate",
    "ModuleProgressSummary",
    "ModuleRead",
    "ModuleUpdate",
    "NotificationListResponse",
    "NotificationRead",
    "QuestionCreate",
    "QuestionRead",
    "QuizAttemptRead",
    "QuizCreate",
    "QuizRead",
    "QuizSubmitRequest",
    "QuizSubmitResponse",
    "UserCreate",
    "UserRead",
    "UserUpdate",
]
