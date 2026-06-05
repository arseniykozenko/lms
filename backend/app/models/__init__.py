"""Model package."""
from app.models.assignment import (
    Assignment,
    AssignmentAttachment,
    AssignmentSubmission,
    AssignmentSubmissionAttachment,
    SubmissionStatus,
)
from app.models.admin_audit_log import AdminAuditLog
from app.models.chat_message import ChatMessage
from app.models.chat_group import ChatGroup, ChatGroupMember, ChatGroupMessage
from app.models.comment import Comment
from app.models.content_progress import ContentProgress
from app.models.course_collaborator import CourseCollaborator, CourseCollaboratorStatus
from app.models.course import Course
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.module import Module
from app.models.module_content import ModuleContent
from app.models.notification import Notification, NotificationType
from app.models.quiz import Question, Quiz, QuizAnswer, QuizAttempt
from app.models.report import Report, ReportStatus, ReportTargetType
from app.models.user import User, UserRole

__all__ = [
    "AdminAuditLog",
    "Comment",
    "ContentProgress",
    "CourseCollaborator",
    "CourseCollaboratorStatus",
    "Course",
    "Assignment",
    "AssignmentAttachment",
    "AssignmentSubmission",
    "AssignmentSubmissionAttachment",
    "ChatMessage",
    "ChatGroup",
    "ChatGroupMember",
    "ChatGroupMessage",
    "Enrollment",
    "EnrollmentStatus",
    "Module",
    "ModuleContent",
    "Notification",
    "NotificationType",
    "Question",
    "Quiz",
    "QuizAnswer",
    "QuizAttempt",
    "Report",
    "ReportStatus",
    "ReportTargetType",
    "SubmissionStatus",
    "User",
    "UserRole",
]
