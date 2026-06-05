from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status

from app.core.security.dependencies import get_current_active_user, get_optional_current_user, require_teacher
from app.schemas.course import CourseCollaboratorInviteCreate, CourseCollaboratorRead, CourseCreate, CourseRead, CourseUpdate
from app.schemas.ai_insights import CourseAiInsightsResponse, StudentAiInsightsResponse
from app.schemas.enrollment import CourseStudentEnrollmentRead, EnrollmentRead
from app.schemas.module import ModuleRead
from app.schemas.user import UserRead
from app.services.courses import CourseService, get_course_service
from app.services.ai_insights import AiInsightsService, get_ai_insights_service
from app.services.modules import ModuleService, get_module_service

router = APIRouter()


@router.get("", response_model=list[CourseRead])
def list_courses(
    q: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=120),
    is_free: bool | None = Query(default=None),
    current_user: UserRead | None = Depends(get_optional_current_user),
    course_service: CourseService = Depends(get_course_service),
) -> list[CourseRead]:
    return course_service.list_courses(current_user, query=q, category=category, is_free=is_free)


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
) -> CourseRead:
    return course_service.create_course(payload, current_user)


@router.get("/categories/list", response_model=list[str])
def list_course_categories(
    current_user: UserRead | None = Depends(get_optional_current_user),
    course_service: CourseService = Depends(get_course_service),
) -> list[str]:
    return course_service.list_categories(current_user)


@router.get("/{course_id}", response_model=CourseRead)
def get_course(
    course_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    course_service: CourseService = Depends(get_course_service),
) -> CourseRead:
    return course_service.get_course(course_id, current_user)


@router.patch("/{course_id}", response_model=CourseRead)
def update_course(
    course_id: UUID,
    payload: CourseUpdate,
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
) -> CourseRead:
    return course_service.update_course(course_id, payload, current_user)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: UUID,
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
) -> Response:
    course_service.delete_course(course_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{course_id}/thumbnail", response_model=CourseRead)
def upload_course_thumbnail(
    course_id: UUID,
    file: UploadFile = File(...),
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
) -> CourseRead:
    return course_service.upload_thumbnail(course_id, file, current_user)


@router.post("/{course_id}/enroll", response_model=EnrollmentRead, status_code=status.HTTP_201_CREATED)
def enroll_course(
    course_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    course_service: CourseService = Depends(get_course_service),
) -> EnrollmentRead:
    return course_service.enroll(course_id, current_user)


@router.get("/{course_id}/students", response_model=list[CourseStudentEnrollmentRead])
def list_course_students(
    course_id: UUID,
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
) -> list[CourseStudentEnrollmentRead]:
    return course_service.list_course_students(course_id, current_user)


@router.get("/{course_id}/students.csv")
def export_course_students_csv(
    course_id: UUID,
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
) -> Response:
    csv_text = course_service.export_course_students_csv(course_id, current_user)
    filename = f"course_{course_id}_students.csv"
    return Response(
        content=f"\ufeff{csv_text}",
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{course_id}/analytics.zip")
def export_course_analytics_zip(
    course_id: UUID,
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
) -> Response:
    archive = course_service.export_course_analytics_zip(course_id, current_user)
    filename = f"course_{course_id}_analytics.zip"
    return Response(
        content=archive,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{course_id}/ai-insights", response_model=CourseAiInsightsResponse)
def get_course_ai_insights(
    course_id: UUID,
    students_limit: int = Query(default=15, ge=3, le=50),
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
    ai_insights_service: AiInsightsService = Depends(get_ai_insights_service),
) -> CourseAiInsightsResponse:
    course = course_service.ensure_can_manage_course(course_id, current_user)
    return ai_insights_service.generate_course_insights(
        course=course,
        current_user=current_user,
        students_limit=students_limit,
    )


@router.get("/{course_id}/ai-insights/student", response_model=StudentAiInsightsResponse)
def get_student_course_ai_insights(
    course_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    course_service: CourseService = Depends(get_course_service),
    ai_insights_service: AiInsightsService = Depends(get_ai_insights_service),
) -> StudentAiInsightsResponse:
    if not course_service.has_course_access(course_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    course = course_service.get_course(course_id, current_user)
    return ai_insights_service.generate_student_insights(course=course, current_user=current_user)


@router.delete("/{course_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_course_student(
    course_id: UUID,
    student_id: UUID,
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
) -> Response:
    course_service.remove_student(course_id, student_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{course_id}/modules", response_model=list[ModuleRead])
def list_course_modules(
    course_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    module_service: ModuleService = Depends(get_module_service),
) -> list[ModuleRead]:
    return module_service.list_course_modules(course_id, current_user)


@router.post("/{course_id}/collaborators/invite", response_model=CourseCollaboratorRead, status_code=status.HTTP_201_CREATED)
def invite_course_collaborator(
    course_id: UUID,
    payload: CourseCollaboratorInviteCreate,
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
) -> CourseCollaboratorRead:
    return course_service.invite_course_collaborator(course_id, payload, current_user)


@router.get("/{course_id}/collaborators", response_model=list[CourseCollaboratorRead])
def list_course_collaborators(
    course_id: UUID,
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
) -> list[CourseCollaboratorRead]:
    return course_service.list_course_collaborators(course_id, current_user)


@router.delete("/{course_id}/collaborators/{collaborator_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_course_collaborator(
    course_id: UUID,
    collaborator_user_id: UUID,
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
) -> Response:
    course_service.remove_course_collaborator(course_id, collaborator_user_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/collaboration-invites/me", response_model=list[CourseCollaboratorRead])
def list_my_collaboration_invites(
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
) -> list[CourseCollaboratorRead]:
    return course_service.list_my_collaboration_invites(current_user)


@router.post("/collaboration-invites/{invite_id}/accept", response_model=CourseCollaboratorRead)
def accept_collaboration_invite(
    invite_id: UUID,
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
) -> CourseCollaboratorRead:
    return course_service.accept_course_collaboration_invite(invite_id, current_user)


@router.post("/collaboration-invites/{invite_id}/decline", response_model=CourseCollaboratorRead)
def decline_collaboration_invite(
    invite_id: UUID,
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
) -> CourseCollaboratorRead:
    return course_service.decline_course_collaboration_invite(invite_id, current_user)
