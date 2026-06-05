"""Service package."""
from app.services.analytics import AnalyticsService
from app.services.ai_insights import AiInsightsService
from app.services.auth import AuthService
from app.services.chat import ChatService
from app.services.comments import CommentService
from app.services.courses import CourseService
from app.services.media import MediaService
from app.services.modules import ModuleService
from app.services.quizzes import QuizService
from app.services.users import UserService

__all__ = [
    "AnalyticsService",
    "AiInsightsService",
    "AuthService",
    "ChatService",
    "CommentService",
    "CourseService",
    "MediaService",
    "ModuleService",
    "QuizService",
    "UserService",
]
