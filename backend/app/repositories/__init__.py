"""Repository package."""
from app.repositories.comment import CommentRepository
from app.repositories.course import CourseRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.module import ModuleRepository
from app.repositories.quiz import QuizRepository
from app.repositories.user import UserRepository

__all__ = [
    "CommentRepository",
    "CourseRepository",
    "EnrollmentRepository",
    "ModuleRepository",
    "QuizRepository",
    "UserRepository",
]
