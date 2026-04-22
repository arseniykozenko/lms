from uuid import UUID

from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import UserRole
from app.repositories.course import CourseRepository
from app.repositories.enrollment import EnrollmentRepository
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate
from app.schemas.enrollment import CourseStudentEnrollmentRead, EnrollmentRead
from app.schemas.user import UserRead
from app.services.media import MediaService, get_media_service


class CourseService:
    def __init__(self, db: Session, media: MediaService) -> None:
        self.db = db
        self.courses = CourseRepository(db)
        self.enrollments = EnrollmentRepository(db)
        self.media = media

    def list_courses(self, current_user: UserRead) -> list[CourseRead]:
        courses = self.courses.list_all()
        visible = [
            course
            for course in courses
            if course.is_published or course.author_id == current_user.id or current_user.role == UserRole.ADMIN
        ]
        return [CourseRead.model_validate(course) for course in visible]

    def get_course(self, course_id: UUID, current_user: UserRead) -> CourseRead:
        course = self._get_course_or_404(course_id)
        if not course.is_published and course.author_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Course is not published")
        return CourseRead.model_validate(course)

    def create_course(self, payload: CourseCreate, current_user: UserRead) -> CourseRead:
        if current_user.role not in {UserRole.TEACHER, UserRole.ADMIN}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can create courses")

        course = Course(
            author_id=current_user.id,
            title=payload.title,
            description=payload.description,
            thumbnail_url=self.media.normalize_url(payload.thumbnail_url),
            is_free=payload.is_free,
            is_published=payload.is_published,
        )
        self.courses.create(course)
        self.db.commit()
        self.db.refresh(course)
        return CourseRead.model_validate(course)

    def update_course(self, course_id: UUID, payload: CourseUpdate, current_user: UserRead) -> CourseRead:
        course = self._get_course_for_management(course_id, current_user)
        for field in ("title", "description", "is_free", "is_published"):
            value = getattr(payload, field)
            if value is not None:
                setattr(course, field, value)
        if payload.thumbnail_url is not None:
            course.thumbnail_url = self.media.normalize_url(payload.thumbnail_url)
        self.db.commit()
        self.db.refresh(course)
        return CourseRead.model_validate(course)

    def delete_course(self, course_id: UUID, current_user: UserRead) -> None:
        course = self._get_course_for_management(course_id, current_user)
        self.courses.delete(course)
        self.db.commit()

    def upload_thumbnail(self, course_id: UUID, upload: UploadFile, current_user: UserRead) -> CourseRead:
        course = self._get_course_for_management(course_id, current_user)
        course.thumbnail_url = self.media.upload_course_thumbnail(str(course.id), upload)
        self.db.commit()
        self.db.refresh(course)
        return CourseRead.model_validate(course)

    def enroll(self, course_id: UUID, current_user: UserRead) -> EnrollmentRead:
        course = self._get_course_or_404(course_id)
        existing = self.enrollments.get_by_user_and_course(current_user.id, course.id)
        if existing is not None:
            return EnrollmentRead.model_validate(existing)
        enrollment = Enrollment(user_id=current_user.id, course_id=course.id)
        self.enrollments.create(enrollment)
        self.db.commit()
        self.db.refresh(enrollment)
        return EnrollmentRead.model_validate(enrollment)

    def list_course_students(self, course_id: UUID, current_user: UserRead) -> list[CourseStudentEnrollmentRead]:
        course = self._get_course_for_management(course_id, current_user)
        enrollments = self.enrollments.list_by_course(course.id)
        return [CourseStudentEnrollmentRead.model_validate(enrollment) for enrollment in enrollments]

    def remove_student(self, course_id: UUID, student_id: UUID, current_user: UserRead) -> None:
        course = self._get_course_for_management(course_id, current_user)
        enrollment = self.enrollments.get_by_user_and_course(student_id, course.id)
        if enrollment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
        self.enrollments.delete(enrollment)
        self.db.commit()

    def has_course_access(self, course_id: UUID, current_user: UserRead) -> bool:
        course = self._get_course_or_404(course_id)
        if current_user.role == UserRole.ADMIN or course.author_id == current_user.id:
            return True
        return self.enrollments.get_by_user_and_course(current_user.id, course_id) is not None

    def _get_course_or_404(self, course_id: UUID) -> Course:
        course = self.courses.get_by_id(course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        return course

    def _get_course_for_management(self, course_id: UUID, current_user: UserRead) -> Course:
        course = self._get_course_or_404(course_id)
        if current_user.role == UserRole.ADMIN:
            return course
        if current_user.role != UserRole.TEACHER or course.author_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return course


def get_course_service(
    db: Session = Depends(get_db),
    media: MediaService = Depends(get_media_service),
) -> CourseService:
    return CourseService(db, media)
