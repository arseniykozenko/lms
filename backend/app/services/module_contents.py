import json
from datetime import UTC, datetime
from pathlib import Path
from urllib import parse, request
from uuid import UUID

from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
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
from app.services.progress import ProgressService, get_progress_service


class ModuleContentService:
    def __init__(self, db: Session, media: MediaService, courses: CourseService, progress: ProgressService) -> None:
        self.db = db
        self.media = media
        self.courses = courses
        self.progress = progress
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
        self.courses.ensure_can_delete_course_resources(content.module.course_id, current_user)
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

    def mark_content_viewed(self, content_id: UUID, current_user: UserRead) -> None:
        content = self.contents.get_by_id(content_id)
        if content is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module content not found")
        module = self._get_module_or_404(content.module_id)
        self._ensure_module_view_access(module, current_user)
        self.progress.mark_content_viewed(content.id, current_user)

    def generate_transcript(self, content_id: UUID, current_user: UserRead) -> ModuleContentRead:
        content = self.contents.get_by_id(content_id)
        if content is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module content not found")
        module = self._get_module_or_404(content.module_id)
        self._ensure_module_view_access(module, current_user)
        if content.content_type != ModuleContentType.VIDEO:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="AI summary is available for video content only")
        if not settings.groq_api_key:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GROQ_API_KEY is not configured")

        content.transcript_status = "processing"
        content.transcript_error = None
        content.transcript_updated_at = datetime.now(UTC)
        self.db.commit()

        try:
            if not content.asset_url:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Video file URL is missing")
            file_name, file_bytes = self._read_asset_bytes(content.asset_url)
            transcript_text, raw_segments = self._transcribe_with_groq(file_name=file_name, file_bytes=file_bytes)
            timestamps = self._build_timestamps(raw_segments)
            summary, refined_timestamps = self._summarize_transcript(transcript_text, timestamps, content.title)
            content.transcript_text = transcript_text.strip() or None
            content.transcript_summary = summary or None
            content.transcript_timestamps_json = refined_timestamps or timestamps or []
            content.transcript_status = "completed" if content.transcript_text else "failed"
            content.transcript_error = None if content.transcript_text else "Empty transcript"
            content.transcript_updated_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(content)
            return ModuleContentRead.model_validate(content)
        except HTTPException:
            raise
        except Exception as exc:
            content.transcript_status = "failed"
            content.transcript_error = str(exc)[:500]
            content.transcript_summary = None
            content.transcript_timestamps_json = []
            content.transcript_updated_at = datetime.now(UTC)
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Transcription failed: {exc}") from exc

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
        if (
            not module.is_published
            and current_user.role != UserRole.ADMIN
            and module.course.author_id != current_user.id
            and not self.courses.is_course_collaborator(module.course_id, current_user.id)
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Module is not published")

    def _get_module_for_management(self, module_id: UUID, current_user: UserRead) -> Module:
        module = self._get_module_or_404(module_id)
        self.courses.ensure_can_manage_course(module.course_id, current_user)
        return module

    def _get_content_for_management(self, content_id: UUID, current_user: UserRead) -> ModuleContent:
        content = self.contents.get_by_id(content_id)
        if content is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module content not found")
        self._get_module_for_management(content.module_id, current_user)
        return content

    def _read_asset_bytes(self, asset_url: str) -> tuple[str, bytes]:
        parsed = parse.urlparse(asset_url)
        name = Path(parsed.path).name or "lecture-video.mp4"
        local_prefix = settings.local_media_url_prefix.strip("/")
        parsed_path = parsed.path.strip("/")
        media_path_candidate = None
        if local_prefix and parsed_path.startswith(local_prefix):
            relative = parsed_path[len(local_prefix):].lstrip("/")
            media_path_candidate = Path(settings.local_media_path) / relative
        if media_path_candidate and media_path_candidate.exists():
            return name, media_path_candidate.read_bytes()

        with request.urlopen(asset_url, timeout=45) as response:
            return name, response.read()

    def _transcribe_with_groq(self, *, file_name: str, file_bytes: bytes) -> tuple[str, list[dict]]:
        try:
            from groq import Groq
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"GROQ SDK is not installed: {exc}") from exc

        client = Groq(api_key=settings.groq_api_key)
        result = client.audio.transcriptions.create(
            model=settings.groq_transcription_model,
            file=(file_name, file_bytes),
            response_format="verbose_json",
        )
        text = getattr(result, "text", None)
        segments = getattr(result, "segments", None)
        if segments is None and isinstance(result, dict):
            segments = result.get("segments")
        if text:
            return text, list(segments or [])
        if isinstance(result, dict):
            return str(result.get("text") or ""), list(result.get("segments") or [])
        return "", []

    def _build_timestamps(self, segments: list[dict]) -> list[dict]:
        if not segments:
            return []
        normalized: list[dict] = []
        for segment in segments:
            start = float(segment.get("start", 0) or 0)
            end = float(segment.get("end", start) or start)
            text = str(segment.get("text", "") or "").strip()
            if end < start:
                end = start
            if not text:
                continue
            normalized.append({"start": start, "end": end, "text": text})

        if not normalized:
            return []

        total_duration = max(item["end"] for item in normalized)
        # Крупные блоки по всей длительности: от 4 до 12 чанков.
        target_chunks = max(4, min(12, int(total_duration // 45) + 1))
        chunk_size = max(20.0, total_duration / target_chunks)

        buckets: list[dict] = []
        chunk_start = 0.0
        while chunk_start < total_duration + 0.01:
            chunk_end = min(total_duration, chunk_start + chunk_size)
            chunk_items = [
                item for item in normalized
                if not (item["end"] < chunk_start or item["start"] > chunk_end)
            ]
            if chunk_items:
                combined = " ".join(item["text"] for item in chunk_items)
                buckets.append(
                    {
                        "start_sec": round(chunk_start, 2),
                        "end_sec": round(chunk_end, 2),
                        "label": combined[:220],
                    }
                )
            chunk_start = chunk_end
            if chunk_end >= total_duration:
                break

        return buckets

    def _summarize_transcript(self, transcript_text: str, timestamps: list[dict], title: str) -> tuple[str, list[dict]]:
        if not transcript_text.strip():
            return "", timestamps

        try:
            from groq import Groq
        except Exception:
            return "", timestamps
        client = Groq(api_key=settings.groq_api_key)
        system_prompt = (
            "Ты помощник по обучению. Составь структурированный конспект видео-лекции на русском и краткие смысловые таймкоды. "
            "Таймкод должен описывать, о чем идет речь в фрагменте, а не дословно повторять текст спикера. "
            "Конспект должен быть содержательным: минимум 4 пункта, 2-4 предложения в каждом пункте. "
            "Избегай пустых общих фраз и повторения названия лекции как единственного содержания. "
            "Верни только JSON без markdown формата: "
            "{\"summary\":\"...\",\"timeline\":[{\"start_sec\":0,\"end_sec\":15,\"topic\":\"...\"}]}"
        )
        payload = {
            "lecture_title": title,
            "timestamps": timestamps[:24],
            "transcript_excerpt": transcript_text[:18000],
        }
        completion = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            temperature=0.2,
            max_completion_tokens=900,
            top_p=1,
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content or "{}"
        try:
            parsed = json.loads(content)
            summary = str(parsed.get("summary") or "").strip()
            timeline_raw = parsed.get("timeline") or []
            timeline: list[dict] = []
            for item in timeline_raw:
                try:
                    start_sec = round(float(item.get("start_sec", 0) or 0), 2)
                    end_sec = round(float(item.get("end_sec", start_sec) or start_sec), 2)
                    topic = str(item.get("topic") or "").strip()
                except Exception:
                    continue
                if not topic:
                    continue
                timeline.append(
                    {
                        "start_sec": start_sec,
                        "end_sec": end_sec,
                        "label": topic[:140],
                    }
                )
            if self._is_weak_summary(summary, title):
                summary = self._build_summary_from_timestamps(title, timeline or timestamps)

            # Если модель вернула мало/коротко, не теряем полноту покрытия.
            if not timeline:
                return summary, timestamps
            last_ai_end = max(point["end_sec"] for point in timeline)
            last_raw_end = max(point["end_sec"] for point in timestamps) if timestamps else 0
            if last_ai_end + 5 < last_raw_end:
                return summary, timestamps
            return summary, timeline
        except Exception:
            return self._build_summary_from_timestamps(title, timestamps), timestamps

    def _is_weak_summary(self, summary: str, title: str) -> bool:
        if not summary:
            return True
        cleaned = " ".join(summary.split()).strip().lower()
        title_cleaned = " ".join((title or "").split()).strip().lower()
        if len(cleaned) < 80:
            return True
        if cleaned == title_cleaned:
            return True
        if cleaned.rstrip(".!?:;,-") == title_cleaned.rstrip(".!?:;,-"):
            return True
        return False

    def _build_summary_from_timestamps(self, title: str, timestamps: list[dict]) -> str:
        if not timestamps:
            return f"В уроке «{title}» рассматривается основная тема занятия, ключевые термины и практические примеры применения материала."

        topics = [str(item.get("label") or "").strip() for item in timestamps[:6] if str(item.get("label") or "").strip()]
        if not topics:
            return f"В уроке «{title}» разбираются ключевые идеи темы, последовательность действий и практические рекомендации по применению материала."

        intro = f"В видеоуроке «{title}» последовательно разбираются ключевые аспекты темы."
        middle = "Сначала рассматриваются базовые понятия и их роль, затем объясняются основные подходы и типичные сценарии применения."
        end = "В завершение акцент сделан на практических шагах, частых ошибках и том, как использовать материал в реальных задачах."
        topical = f"Среди центральных акцентов урока: {', '.join(topics[:4])}."
        return " ".join([intro, middle, topical, end])


def get_module_content_service(
    db: Session = Depends(get_db),
    media: MediaService = Depends(get_media_service),
    courses: CourseService = Depends(get_course_service),
    progress: ProgressService = Depends(get_progress_service),
) -> ModuleContentService:
    return ModuleContentService(db, media, courses, progress)
