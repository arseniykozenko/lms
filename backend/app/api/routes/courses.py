from uuid import UUID

from fastapi import APIRouter, Depends, File, Response, UploadFile, status

from app.core.security.dependencies import get_current_active_user, require_teacher
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate
from app.schemas.enrollment import CourseStudentEnrollmentRead, EnrollmentRead
from app.schemas.module import ModuleRead
from app.schemas.user import UserRead
from app.services.courses import CourseService, get_course_service
from app.services.modules import ModuleService, get_module_service

router = APIRouter()


@router.get("", response_model=list[CourseRead])
def list_courses(
    current_user: UserRead = Depends(get_current_active_user),
    course_service: CourseService = Depends(get_course_service),
) -> list[CourseRead]:
    return course_service.list_courses(current_user)


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    current_user: UserRead = Depends(require_teacher),
    course_service: CourseService = Depends(get_course_service),
) -> CourseRead:
    return course_service.create_course(payload, current_user)


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
