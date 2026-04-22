from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.security.dependencies import get_current_active_user, require_teacher
from app.schemas.quiz import QuizAttemptRead, QuizCreate, QuizRead, QuizSubmitRequest, QuizSubmitResponse, QuizUpdate
from app.schemas.user import UserRead
from app.services.quizzes import QuizService, get_quiz_service

router = APIRouter()


@router.post("/modules/{module_id}/quiz", response_model=QuizRead, status_code=status.HTTP_201_CREATED)
def create_quiz(
    module_id: UUID,
    payload: QuizCreate,
    current_user: UserRead = Depends(require_teacher),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> QuizRead:
    return quiz_service.create_quiz(module_id, payload, current_user)


@router.get("/modules/{module_id}/quiz", response_model=QuizRead)
def get_module_quiz(
    module_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> QuizRead:
    return quiz_service.get_module_quiz(module_id, current_user)


@router.get("/quizzes/{quiz_id}", response_model=QuizRead)
def get_quiz(
    quiz_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> QuizRead:
    return quiz_service.get_quiz(quiz_id, current_user)


@router.patch("/quizzes/{quiz_id}", response_model=QuizRead)
def update_quiz(
    quiz_id: UUID,
    payload: QuizUpdate,
    current_user: UserRead = Depends(require_teacher),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> QuizRead:
    return quiz_service.update_quiz(quiz_id, payload, current_user)


@router.delete("/quizzes/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(
    quiz_id: UUID,
    current_user: UserRead = Depends(require_teacher),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> None:
    quiz_service.delete_quiz(quiz_id, current_user)


@router.post("/quizzes/{quiz_id}/submit", response_model=QuizSubmitResponse)
def submit_quiz(
    quiz_id: UUID,
    payload: QuizSubmitRequest,
    current_user: UserRead = Depends(get_current_active_user),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> QuizSubmitResponse:
    return quiz_service.submit_quiz(quiz_id, payload, current_user)


@router.get("/quizzes/{quiz_id}/attempts/me", response_model=list[QuizAttemptRead])
def list_my_attempts(
    quiz_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> list[QuizAttemptRead]:
    return quiz_service.list_my_attempts(quiz_id, current_user)
