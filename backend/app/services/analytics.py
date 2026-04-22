from datetime import UTC, date, timedelta

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.analytics import AnalyticsOverview, DailyEnrollmentPoint


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def overview(self) -> AnalyticsOverview:
        users = self.db.scalar(select(func.count()).select_from(User)) or 0
        courses = self.db.scalar(select(func.count()).select_from(Course)) or 0
        enrollments = self.db.scalar(select(func.count()).select_from(Enrollment)) or 0
        return AnalyticsOverview(users=users, courses=courses, enrollments=enrollments)

    def daily_enrollments(self, start_date: date, end_date: date) -> list[DailyEnrollmentPoint]:
        stmt = select(Enrollment.enrolled_at).where(Enrollment.enrolled_at.is_not(None))
        rows: dict[str, int] = {}
        for enrolled_at in self.db.scalars(stmt):
            if getattr(enrolled_at, "tzinfo", None) is None:
                enrolled_at = enrolled_at.replace(tzinfo=UTC)
            enrolled_date = enrolled_at.astimezone().date()
            if start_date <= enrolled_date <= end_date:
                key = enrolled_date.isoformat()
                rows[key] = rows.get(key, 0) + 1

        result = []
        current = start_date
        while current <= end_date:
            key = current.isoformat()
            result.append(DailyEnrollmentPoint(date=key, enrollments=rows.get(key, 0)))
            current += timedelta(days=1)
        return result


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)
