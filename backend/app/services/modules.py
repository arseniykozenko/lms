from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.models.module import Module
from app.models.user import UserRole
from app.repositories.course import CourseRepository
from app.repositories.module import ModuleRepository
from app.schemas.module import ModuleCreate, ModuleRead, ModuleReorderRequest, ModuleUpdate
from app.schemas.user import UserRead
from app.services.courses import CourseService, get_course_service
from app.services.media import MediaService, get_media_service


class ModuleService:
    def __init__(self, db: Session, media: MediaService, courses: CourseService) -> None:
        self.db = db
        self.modules = ModuleRepository(db)
        self.course_repo = CourseRepository(db)
        self.media = media
        self.courses = courses

    def create_module(self, payload: ModuleCreate, current_user: UserRead) -> ModuleRead:
        course = self.course_repo.get_by_id(payload.course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        self._ensure_manage_course(course.author_id, current_user)
        modules = self.modules.list_by_course(payload.course_id)
        module = Module(
            course_id=payload.course_id,
            title=payload.title,
            description=payload.description,
            video_url=self.media.normalize_url(payload.video_url),
            position=len(modules) + 1,
            is_published=payload.is_published,
        )
        self.modules.create(module)
        self.db.commit()
        self.db.refresh(module)
        return self._to_module_read(module)

    def get_module(self, module_id: UUID, current_user: UserRead) -> ModuleRead:
        module = self._get_module_or_404(module_id)
        if not self.courses.has_course_access(module.course_id, current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not enrolled in this course")
        if not module.is_published and current_user.role != UserRole.ADMIN and module.course.author_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Module is not published")
        return self._to_module_read(module)

    def list_course_modules(self, course_id: UUID, current_user: UserRead) -> list[ModuleRead]:
        if not self.courses.has_course_access(course_id, current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not enrolled in this course")
        modules = self.modules.list_by_course(course_id)
        visible = [
            module
            for module in modules
            if module.is_published or current_user.role == UserRole.ADMIN or module.course.author_id == current_user.id
        ]
        return [self._to_module_read(module) for module in visible]

    def update_module(self, module_id: UUID, payload: ModuleUpdate, current_user: UserRead) -> ModuleRead:
        module = self._get_module_or_404(module_id)
        self._ensure_manage_course(module.course.author_id, current_user)
        for field in ("title", "description", "is_published"):
            value = getattr(payload, field)
            if value is not None:
                setattr(module, field, value)
        if payload.video_url is not None:
            module.video_url = self.media.normalize_url(payload.video_url)
        self.db.commit()
        self.db.refresh(module)
        return self._to_module_read(module)

    def reorder_modules(self, course_id: UUID, payload: ModuleReorderRequest, current_user: UserRead) -> list[ModuleRead]:
        course = self.course_repo.get_by_id(course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        self._ensure_manage_course(course.author_id, current_user)

        modules = self.modules.list_by_course(course_id)
        existing_ids = {module.id for module in modules}
        requested_ids = [item.id for item in payload.modules]

        if len(requested_ids) != len(existing_ids) or set(requested_ids) != existing_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Modules reorder payload must contain every module of the course exactly once",
            )

        module_map = {module.id: module for module in modules}
        for position, module_id in enumerate(requested_ids, start=1):
            module_map[module_id].position = position

        self.db.commit()
        reordered = self.modules.list_by_course(course_id)
        return [self._to_module_read(module) for module in reordered]

    def _get_module_or_404(self, module_id: UUID) -> Module:
        module = self.modules.get_by_id(module_id)
        if module is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
        return module

    def _ensure_manage_course(self, author_id: UUID, current_user: UserRead) -> None:
        if current_user.role == UserRole.ADMIN:
            return
        if current_user.role != UserRole.TEACHER or author_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    def _to_module_read(self, module: Module) -> ModuleRead:
        return ModuleRead(
            id=module.id,
            course_id=module.course_id,
            course_title=module.course.title if module.course is not None else None,
            title=module.title,
            description=module.description,
            video_url=module.video_url,
            position=module.position,
            is_published=module.is_published,
            created_at=module.created_at,
            updated_at=module.updated_at,
        )


def get_module_service(
    db: Session = Depends(get_db),
    media: MediaService = Depends(get_media_service),
    courses: CourseService = Depends(get_course_service),
) -> ModuleService:
    return ModuleService(db, media, courses)
