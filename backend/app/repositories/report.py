from uuid import UUID

from datetime import datetime

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.report import Report, ReportStatus


class ReportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, report: Report) -> Report:
        self.db.add(report)
        self.db.flush()
        return report

    def get_by_id(self, report_id: UUID) -> Report | None:
        stmt = (
            select(Report)
            .options(
                joinedload(Report.reporter),
                joinedload(Report.reviewer),
                joinedload(Report.comment),
                joinedload(Report.module_content),
            )
            .where(Report.id == report_id)
        )
        return self.db.scalar(stmt)

    def list_all(self, *, status: ReportStatus | None = None) -> list[Report]:
        stmt = (
            select(Report)
            .options(
                joinedload(Report.reporter),
                joinedload(Report.reviewer),
                joinedload(Report.comment),
                joinedload(Report.module_content),
            )
            .order_by(Report.created_at.desc())
        )
        if status is not None:
            stmt = stmt.where(Report.status == status)
        return list(self.db.scalars(stmt))

    def get_open_duplicate_for_reporter(self, report: Report) -> Report | None:
        target_filters = [
            Report.target_type == report.target_type,
            Report.reporter_user_id == report.reporter_user_id,
            Report.status.in_([ReportStatus.OPEN, ReportStatus.IN_REVIEW]),
        ]
        if report.course_id is not None:
            target_filters.append(Report.course_id == report.course_id)
        if report.comment_id is not None:
            target_filters.append(Report.comment_id == report.comment_id)
        if report.chat_message_id is not None:
            target_filters.append(Report.chat_message_id == report.chat_message_id)
        if report.module_content_id is not None:
            target_filters.append(Report.module_content_id == report.module_content_id)

        stmt = select(Report).where(and_(*target_filters)).order_by(Report.created_at.desc()).limit(1)
        return self.db.scalar(stmt)

    def delete_closed_reviewed_before(self, reviewed_before: datetime) -> int:
        stmt = delete(Report).where(
            Report.reviewed_at.is_not(None),
            Report.reviewed_at < reviewed_before,
            or_(Report.status == ReportStatus.RESOLVED, Report.status == ReportStatus.REJECTED),
        )
        result = self.db.execute(stmt)
        return int(result.rowcount or 0)
