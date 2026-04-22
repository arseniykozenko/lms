from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from app.core.security.dependencies import get_current_active_user, require_teacher
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentRead,
    AssignmentSubmissionCreate,
    AssignmentSubmissionGrade,
    AssignmentSubmissionRead,
    AssignmentUpdate,
)
from app.schemas.user import UserRead
from app.services.assignments import AssignmentService, get_assignment_service

router = APIRouter()


@router.get("/modules/{module_id}/assignments", response_model=list[AssignmentRead])
def list_module_assignments(
    module_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> list[AssignmentRead]:
    return assignment_service.list_module_assignments(module_id, current_user)


@router.post("/modules/{module_id}/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment(
    module_id: UUID,
    payload: AssignmentCreate,
    current_user: UserRead = Depends(require_teacher),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentRead:
    return assignment_service.create_assignment(module_id, payload, current_user)


@router.get("/assignments/{assignment_id}", response_model=AssignmentRead)
def get_assignment(
    assignment_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentRead:
    return assignment_service.get_assignment(assignment_id, current_user)


@router.patch("/assignments/{assignment_id}", response_model=AssignmentRead)
def update_assignment(
    assignment_id: UUID,
    payload: AssignmentUpdate,
    current_user: UserRead = Depends(require_teacher),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentRead:
    return assignment_service.update_assignment(assignment_id, payload, current_user)


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: UUID,
    current_user: UserRead = Depends(require_teacher),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> Response:
    assignment_service.delete_assignment(assignment_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/assignments/{assignment_id}/attachment", response_model=AssignmentRead)
def upload_assignment_attachment(
    assignment_id: UUID,
    files: list[UploadFile] = File(...),
    current_user: UserRead = Depends(require_teacher),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentRead:
    return assignment_service.upload_assignment_attachment(assignment_id, files, current_user)


@router.get("/assignments/{assignment_id}/submissions/me", response_model=list[AssignmentSubmissionRead])
def list_my_assignment_submissions(
    assignment_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> list[AssignmentSubmissionRead]:
    return assignment_service.list_my_submissions(assignment_id, current_user)


@router.post("/assignments/{assignment_id}/submissions", response_model=AssignmentSubmissionRead, status_code=status.HTTP_201_CREATED)
def create_assignment_submission(
    assignment_id: UUID,
    answer_markdown: str | None = Form(default=None),
    files: list[UploadFile] | None = File(default=None),
    current_user: UserRead = Depends(get_current_active_user),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentSubmissionRead:
    payload = AssignmentSubmissionCreate(answer_markdown=answer_markdown)
    return assignment_service.create_submission(assignment_id, payload, files, current_user)


@router.patch("/assignment-submissions/{submission_id}", response_model=AssignmentSubmissionRead)
def update_assignment_submission(
    submission_id: UUID,
    answer_markdown: str | None = Form(default=None),
    files: list[UploadFile] | None = File(default=None),
    current_user: UserRead = Depends(get_current_active_user),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentSubmissionRead:
    payload = AssignmentSubmissionCreate(answer_markdown=answer_markdown)
    return assignment_service.update_submission(submission_id, payload, files, current_user)


@router.delete("/assignment-submissions/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment_submission(
    submission_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> Response:
    assignment_service.delete_submission(submission_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/assignments/{assignment_id}/submissions", response_model=list[AssignmentSubmissionRead])
def list_assignment_submissions(
    assignment_id: UUID,
    current_user: UserRead = Depends(require_teacher),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> list[AssignmentSubmissionRead]:
    return assignment_service.list_assignment_submissions(assignment_id, current_user)


@router.patch("/assignment-submissions/{submission_id}/grade", response_model=AssignmentSubmissionRead)
def grade_assignment_submission(
    submission_id: UUID,
    payload: AssignmentSubmissionGrade,
    current_user: UserRead = Depends(require_teacher),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentSubmissionRead:
    return assignment_service.grade_submission(submission_id, payload, current_user)
