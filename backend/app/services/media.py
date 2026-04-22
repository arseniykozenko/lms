import base64
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, HTTPException, UploadFile, status

from app.core.config import settings


class MediaService:
    allowed_image_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
    }
    allowed_module_asset_types = {
        "video/mp4": (".mp4", "video"),
        "video/webm": (".webm", "video"),
        "application/pdf": (".pdf", "pdf"),
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": (".pptx", "presentation"),
        "application/msword": (".doc", "document"),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (".docx", "document"),
        "text/plain": (".txt", "document"),
        "application/zip": (".zip", "archive"),
        "application/x-zip-compressed": (".zip", "archive"),
        "application/x-rar-compressed": (".rar", "archive"),
        "application/vnd.rar": (".rar", "archive"),
        "application/x-7z-compressed": (".7z", "archive"),
        "application/octet-stream": (".bin", "binary"),
    }
    allowed_module_asset_extensions = {
        ".mp4": ("video/mp4", ".mp4", "video"),
        ".webm": ("video/webm", ".webm", "video"),
        ".pdf": ("application/pdf", ".pdf", "pdf"),
        ".pptx": (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".pptx",
            "presentation",
        ),
        ".doc": ("application/msword", ".doc", "document"),
        ".docx": (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".docx",
            "document",
        ),
        ".txt": ("text/plain", ".txt", "document"),
        ".zip": ("application/zip", ".zip", "archive"),
        ".rar": ("application/vnd.rar", ".rar", "archive"),
        ".7z": ("application/x-7z-compressed", ".7z", "archive"),
    }

    def normalize_url(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def upload_profile_photo(self, user_id: str, upload: UploadFile) -> str:
        return self._upload_image(
            owner_id=user_id,
            upload=upload,
            local_folder="profile-photos",
            cloudinary_folder="lms/profile-photos",
        )

    def upload_course_thumbnail(self, course_id: str, upload: UploadFile) -> str:
        return self._upload_image(
            owner_id=course_id,
            upload=upload,
            local_folder="course-thumbnails",
            cloudinary_folder="lms/course-thumbnails",
        )

    def upload_module_asset(self, module_id: str, upload: UploadFile, *, requested_kind: str | None = None) -> dict[str, str]:
        asset_meta = self.allowed_module_asset_types.get(upload.content_type or "")
        if asset_meta is None and upload.filename:
            extension = Path(upload.filename).suffix.lower()
            extension_meta = self.allowed_module_asset_extensions.get(extension)
            if extension_meta is not None:
                inferred_content_type, inferred_extension, inferred_kind = extension_meta
                asset_meta = (inferred_extension, inferred_kind)
                if not upload.content_type:
                    upload.content_type = inferred_content_type
        if asset_meta is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Supported formats: MP4, WEBM, PDF, PPTX, DOC, DOCX, TXT, ZIP, RAR and 7Z",
            )

        extension, content_kind = asset_meta
        if requested_kind is not None:
            if requested_kind == "presentation" and content_kind not in {"pdf", "presentation"}:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Presentation supports PPTX files only",
                )
            if requested_kind == "video" and content_kind != "video":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Video content supports MP4 and WEBM only",
                )
            if requested_kind == "pdf" and content_kind != "pdf":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="PDF content supports PDF files only",
                )
            if requested_kind == "assignment" and content_kind not in {"pdf", "archive", "document", "binary"}:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Assignment attachments support PDF, archive and document files",
                )
            if requested_kind == "submission" and content_kind not in {"pdf", "archive", "binary", "presentation", "document"}:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Submission attachments support PDF, archive, document and presentation files",
                )
            if requested_kind == "presentation":
                content_kind = "presentation"
            if requested_kind in {"assignment", "submission"}:
                content_kind = requested_kind
        content = upload.file.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Empty file")
        if len(content) > 100 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File is too large")

        if settings.media_backend == "cloudinary":
            url = self._upload_module_asset_to_cloudinary(
                module_id,
                content,
                extension,
                upload.content_type or "application/octet-stream",
                content_kind,
            )
        else:
            url = self._save_module_asset_locally(module_id, content, extension)

        return {
            "url": url,
            "content_type": content_kind,
        }

    def _upload_image(self, owner_id: str, upload: UploadFile, local_folder: str, cloudinary_folder: str) -> str:
        extension = self.allowed_image_types.get(upload.content_type or "")
        if extension is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Supported formats: JPG and PNG",
            )
        content = upload.file.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Empty file")
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image is too large")

        if settings.media_backend == "cloudinary":
            return self._upload_to_cloudinary(
                owner_id,
                content,
                extension,
                upload.content_type or "image/jpeg",
                cloudinary_folder,
            )
        return self._save_locally(owner_id, content, extension, local_folder)

    def _save_locally(self, owner_id: str, content: bytes, extension: str, local_folder: str) -> str:
        media_root = Path(settings.local_media_path) / local_folder
        media_root.mkdir(parents=True, exist_ok=True)
        for existing_extension in {".jpg", ".png"}:
            existing = media_root / f"{owner_id}{existing_extension}"
            if existing.exists():
                existing.unlink()
        filename = f"{owner_id}{extension}"
        target = media_root / filename
        target.write_bytes(content)
        return f"{settings.backend_public_url.rstrip('/')}{settings.local_media_url_prefix}/{local_folder}/{filename}"

    def _upload_to_cloudinary(
        self,
        owner_id: str,
        content: bytes,
        extension: str,
        content_type: str,
        cloudinary_folder: str,
    ) -> str:
        if not (settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret):
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Cloudinary is not configured")
        try:
            import cloudinary
            import cloudinary.uploader
        except ModuleNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cloudinary dependency is not installed",
            ) from exc

        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )
        encoded = base64.b64encode(content).decode("ascii")
        payload = f"data:{content_type};base64,{encoded}"
        response = cloudinary.uploader.upload(
            payload,
            folder=cloudinary_folder,
            public_id=f"{owner_id}-{uuid4().hex}",
            overwrite=True,
            resource_type="image",
        )
        return str(response["secure_url"])

    def _save_module_asset_locally(self, module_id: str, content: bytes, extension: str) -> str:
        media_root = Path(settings.local_media_path) / "module-assets" / module_id
        media_root.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4().hex}{extension}"
        target = media_root / filename
        target.write_bytes(content)
        return f"{settings.backend_public_url.rstrip('/')}{settings.local_media_url_prefix}/module-assets/{module_id}/{filename}"

    def _upload_module_asset_to_cloudinary(
        self,
        module_id: str,
        content: bytes,
        extension: str,
        content_type: str,
        content_kind: str,
    ) -> str:
        if not (settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret):
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Cloudinary is not configured")
        try:
            import cloudinary
            import cloudinary.uploader
        except ModuleNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cloudinary dependency is not installed",
            ) from exc

        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )
        encoded = base64.b64encode(content).decode("ascii")
        payload = f"data:{content_type};base64,{encoded}"
        response = cloudinary.uploader.upload(
            payload,
            folder="lms/module-assets",
            public_id=f"{module_id}-{uuid4().hex}",
            overwrite=True,
            resource_type="video" if content_kind == "video" else "raw",
            format=extension.removeprefix("."),
        )
        return str(response["secure_url"])


def get_media_service() -> MediaService:
    return MediaService()
