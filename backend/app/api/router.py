from fastapi import APIRouter

from app.api.routes.analytics import router as analytics_router
from app.api.routes.assignments import router as assignments_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.comments import router as comments_router
from app.api.routes.courses import router as courses_router
from app.api.routes.module_contents import router as module_contents_router
from app.api.routes.modules import router as modules_router
from app.api.routes.moderation import router as moderation_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.quizzes import router as quizzes_router
from app.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(notifications_router, prefix="/users", tags=["notifications"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(courses_router, prefix="/courses", tags=["courses"])
api_router.include_router(modules_router, prefix="/modules", tags=["modules"])
api_router.include_router(module_contents_router, tags=["module-contents"])
api_router.include_router(assignments_router, tags=["assignments"])
api_router.include_router(comments_router, tags=["comments"])
api_router.include_router(moderation_router, prefix="/moderation", tags=["moderation"])
api_router.include_router(quizzes_router, tags=["quizzes"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
