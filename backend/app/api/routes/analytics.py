from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.security.dependencies import require_admin
from app.schemas.analytics import AnalyticsOverview, DailyEnrollmentPoint
from app.schemas.user import UserRead
from app.services.analytics import AnalyticsService, get_analytics_service

router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverview)
def get_overview(
    _: UserRead = Depends(require_admin),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsOverview:
    return analytics_service.overview()


@router.get("/enrollments/daily", response_model=list[DailyEnrollmentPoint])
def get_daily_enrollments(
    start_date: date = Query(...),
    end_date: date = Query(...),
    _: UserRead = Depends(require_admin),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> list[DailyEnrollmentPoint]:
    return analytics_service.daily_enrollments(start_date, end_date)
