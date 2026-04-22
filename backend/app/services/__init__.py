"""Service package."""
from app.services.analytics import AnalyticsService
from app.services.auth import AuthService
from app.services.comments import CommentService
from app.services.courses import CourseService
from app.services.media import MediaService
from app.services.modules import ModuleService
from app.services.quizzes import QuizService
from app.services.users import UserService

__all__ = [
    "AnalyticsService",
    "AuthService",
    "CommentService",
    "CourseService",
    "MediaService",
    "ModuleService",
    "QuizService",
    "UserService",
]
