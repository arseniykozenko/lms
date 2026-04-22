"""Schema package."""
from app.schemas.analytics import AnalyticsOverview, DailyEnrollmentPoint
from app.schemas.comment import CommentCreate, CommentRead
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate, EnrolledCourseRead
from app.schemas.enrollment import EnrollmentRead
from app.schemas.module import ModuleCreate, ModuleRead, ModuleUpdate
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
    "AnalyticsOverview",
    "CommentCreate",
    "CommentRead",
    "CourseCreate",
    "CourseRead",
    "CourseUpdate",
    "DailyEnrollmentPoint",
    "EnrollmentRead",
    "EnrolledCourseRead",
    "ModuleCreate",
    "ModuleRead",
    "ModuleUpdate",
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
