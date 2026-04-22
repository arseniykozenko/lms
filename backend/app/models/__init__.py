"""Model package."""
from app.models.assignment import (
    Assignment,
    AssignmentAttachment,
    AssignmentSubmission,
    AssignmentSubmissionAttachment,
    SubmissionStatus,
)
from app.models.comment import Comment
from app.models.course import Course
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.module import Module
from app.models.quiz import Question, Quiz, QuizAnswer, QuizAttempt
from app.models.user import User, UserRole

__all__ = [
    "Comment",
    "Course",
    "Assignment",
    "AssignmentAttachment",
    "AssignmentSubmission",
    "AssignmentSubmissionAttachment",
    "Enrollment",
    "EnrollmentStatus",
    "Module",
    "Question",
    "Quiz",
    "QuizAnswer",
    "QuizAttempt",
    "SubmissionStatus",
    "User",
    "UserRole",
]
