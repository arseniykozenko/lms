from uuid import UUID

from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.models.module import Module
from app.models.module_content import ModuleContent, ModuleContentType
from app.models.user import UserRole
from app.repositories.module import ModuleRepository
from app.repositories.module_content import ModuleContentRepository
from app.schemas.module_content import (
    ModuleContentLinkCreate,
    ModuleContentRead,
    ModuleContentReorderRequest,
    ModuleContentTextCreate,
    ModuleContentUpdate,
)
from app.schemas.user import UserRead
from app.services.courses import CourseService, get_course_service
from app.services.media import MediaService, get_media_service


class ModuleContentService:
    def __init__(self, db: Session, media: MediaService, courses: CourseService) -> None:
        self.db = db
        self.media = media
        self.courses = courses
        self.modules = ModuleRepository(db)
        self.contents = ModuleContentRepository(db)

    def list_module_contents(self, module_id: UUID, current_user: UserRead) -> list[ModuleContentRead]:
        module = self._get_module_or_404(module_id)
        self._ensure_module_view_access(module, current_user)
        contents = self.contents.list_by_module(module.id)
        return [ModuleContentRead.model_validate(content) for content in contents]

    def create_text_content(self, module_id: UUID, payload: ModuleContentTextCreate, current_user: UserRead) -> ModuleContentRead:
        module = self._get_module_for_management(module_id, current_user)
        content = ModuleContent(
            module_id=module.id,
            title=payload.title,
            content_type=ModuleContentType.TEXT,
            position=self._next_position(module.id),
            text_content=payload.text_content,
        )
        self.contents.create(content)
        self.db.commit()
        self.db.refresh(content)
        return ModuleContentRead.model_validate(content)

    def create_link_content(self, module_id: UUID, payload: ModuleContentLinkCreate, current_user: UserRead) -> ModuleContentRead:
        module = self._get_module_for_management(module_id, current_user)
        content = ModuleContent(
            module_id=module.id,
            title=payload.title,
            content_type=ModuleContentType.LINK,
            position=self._next_position(module.id),
            source_url=self.media.normalize_url(payload.source_url),
        )
        self.contents.create(content)
        self.db.commit()
        self.db.refresh(content)
        return ModuleContentRead.model_validate(content)

    def create_file_content(
        self,
        module_id: UUID,
        title: str,
        upload: UploadFile,
        requested_type: str,
        current_user: UserRead,
    ) -> ModuleContentRead:
        module = self._get_module_for_management(module_id, current_user)
        if not title.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Title is required")
        if requested_type not in {
            ModuleContentType.VIDEO.value,
            ModuleContentType.PDF.value,
            ModuleContentType.PRESENTATION.value,
        }:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported file content type")

        asset = self.media.upload_module_asset(str(module.id), upload, requested_kind=requested_type)
        content = ModuleContent(
            module_id=module.id,
            title=title.strip(),
            content_type=asset["content_type"],
            position=self._next_position(module.id),
            asset_url=asset["url"],
        )
        self.contents.create(content)
        self.db.commit()
        self.db.refresh(content)
        return ModuleContentRead.model_validate(content)

    def update_content(self, content_id: UUID, payload: ModuleContentUpdate, current_user: UserRead) -> ModuleContentRead:
        content = self._get_content_for_management(content_id, current_user)
        if payload.title is not None:
            content.title = payload.title
        if content.content_type == ModuleContentType.TEXT and payload.text_content is not None:
            content.text_content = payload.text_content
        if content.content_type == ModuleContentType.LINK and payload.source_url is not None:
            content.source_url = self.media.normalize_url(payload.source_url)
        self.db.commit()
        self.db.refresh(content)
        return ModuleContentRead.model_validate(content)

    def replace_file_content(
        self,
        content_id: UUID,
        title: str,
        upload: UploadFile,
        current_user: UserRead,
    ) -> ModuleContentRead:
        content = self._get_content_for_management(content_id, current_user)
        if content.content_type not in {
            ModuleContentType.VIDEO,
            ModuleContentType.PDF,
            ModuleContentType.PRESENTATION,
        }:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Only file-based content can replace its file",
            )

        normalized_title = title.strip()
        if not normalized_title:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Title is required")

        asset = self.media.upload_module_asset(
            str(content.module_id),
            upload,
            requested_kind=content.content_type.value,
        )
        content.title = normalized_title
        content.asset_url = asset["url"]
        content.content_type = asset["content_type"]
        self.db.commit()
        self.db.refresh(content)
        return ModuleContentRead.model_validate(content)

    def delete_content(self, content_id: UUID, current_user: UserRead) -> None:
        content = self._get_content_for_management(content_id, current_user)
        self.contents.delete(content)
        self.db.commit()
        self._renumber_positions(content.module_id)

    def reorder_contents(self, module_id: UUID, payload: ModuleContentReorderRequest, current_user: UserRead) -> list[ModuleContentRead]:
        module = self._get_module_for_management(module_id, current_user)
        contents = self.contents.list_by_module(module.id)
        existing_ids = {content.id for content in contents}
        requested_ids = [item.id for item in payload.contents]

        if len(requested_ids) != len(existing_ids) or set(requested_ids) != existing_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Contents reorder payload must contain every content item exactly once",
            )

        content_map = {content.id: content for content in contents}
        for position, content_id in enumerate(requested_ids, start=1):
            content_map[content_id].position = position

        self.db.commit()
        reordered = self.contents.list_by_module(module.id)
        return [ModuleContentRead.model_validate(content) for content in reordered]

    def _next_position(self, module_id: UUID) -> int:
        return len(self.contents.list_by_module(module_id)) + 1

    def _renumber_positions(self, module_id: UUID) -> None:
        contents = self.contents.list_by_module(module_id)
        for position, content in enumerate(contents, start=1):
            content.position = position
        self.db.commit()

    def _get_module_or_404(self, module_id: UUID) -> Module:
        module = self.modules.get_by_id(module_id)
        if module is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
        return module

    def _ensure_module_view_access(self, module: Module, current_user: UserRead) -> None:
        if not self.courses.has_course_access(module.course_id, current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not enrolled in this course")
        if not module.is_published and current_user.role != UserRole.ADMIN and module.course.author_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Module is not published")

    def _get_module_for_management(self, module_id: UUID, current_user: UserRead) -> Module:
        module = self._get_module_or_404(module_id)
        if current_user.role == UserRole.ADMIN:
            return module
        if current_user.role != UserRole.TEACHER or module.course.author_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return module

    def _get_content_for_management(self, content_id: UUID, current_user: UserRead) -> ModuleContent:
        content = self.contents.get_by_id(content_id)
        if content is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module content not found")
        self._get_module_for_management(content.module_id, current_user)
        return content


def get_module_content_service(
    db: Session = Depends(get_db),
    media: MediaService = Depends(get_media_service),
    courses: CourseService = Depends(get_course_service),
) -> ModuleContentService:
    return ModuleContentService(db, media, courses)
