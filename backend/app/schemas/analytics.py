from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    users: int
    courses: int
    enrollments: int


class DailyEnrollmentPoint(BaseModel):
    date: str
    enrollments: int
