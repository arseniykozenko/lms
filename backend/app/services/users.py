from fastapi import Depends, UploadFile
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.models.user import UserRole
from app.repositories.course import CourseRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.user import UserRepository
from app.schemas.course import EnrolledCourseRead
from app.schemas.user import UserRead, UserUpdate
from app.services.media import MediaService, get_media_service


class UserService:
    def __init__(self, db: Session, media: MediaService) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.courses = CourseRepository(db)
        self.enrollments = EnrollmentRepository(db)
        self.media = media

    def get_me(self, current_user: UserRead) -> UserRead:
        user = self.users.get_by_id(current_user.id)
        if user is None:
            return current_user
        return UserRead.model_validate(user)

    def update_me(self, current_user: UserRead, payload: UserUpdate) -> UserRead:
        user = self.users.get_by_id(current_user.id)
        if user is None:
            return current_user
        self.users.update_profile(
            user,
            full_name=payload.full_name,
            profile_photo_url=self.media.normalize_url(payload.profile_photo_url),
        )
        self.db.commit()
        self.db.refresh(user)
        return UserRead.model_validate(user)

    def upload_profile_photo(self, current_user: UserRead, upload: UploadFile) -> UserRead:
        user = self.users.get_by_id(current_user.id)
        if user is None:
            return current_user
        photo_url = self.media.upload_profile_photo(str(current_user.id), upload)
        self.users.update_profile(
            user,
            full_name=user.full_name,
            profile_photo_url=photo_url,
        )
        self.db.commit()
        self.db.refresh(user)
        return UserRead.model_validate(user)

    def list_my_courses(self, current_user: UserRead) -> list[EnrolledCourseRead]:
        if current_user.role in {UserRole.TEACHER, UserRole.ADMIN}:
            courses = self.courses.list_by_author(current_user.id)
            return [
                EnrolledCourseRead(
                    id=course.id,
                    author_id=course.author_id,
                    title=course.title,
                    description=course.description,
                    thumbnail_url=course.thumbnail_url,
                    is_free=course.is_free,
                    is_published=course.is_published,
                    created_at=course.created_at,
                    updated_at=course.updated_at,
                    enrolled_at=course.created_at,
                )
                for course in courses
            ]

        enrollments = self.enrollments.list_by_user(current_user.id)
        result: list[EnrolledCourseRead] = []
        for enrollment in enrollments:
            course = enrollment.course
            if not course.is_published:
                continue
            result.append(
                EnrolledCourseRead(
                    id=course.id,
                    author_id=course.author_id,
                    title=course.title,
                    description=course.description,
                    thumbnail_url=course.thumbnail_url,
                    is_free=course.is_free,
                    is_published=course.is_published,
                    created_at=course.created_at,
                    updated_at=course.updated_at,
                    enrolled_at=enrollment.enrolled_at,
                )
            )
        return result


def get_user_service(
    db: Session = Depends(get_db),
    media: MediaService = Depends(get_media_service),
) -> UserService:
    return UserService(db, media)
