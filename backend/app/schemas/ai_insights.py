from typing import Literal
from pydantic import BaseModel, Field


class AiGroupAction(BaseModel):
    action: str
    why: str
    expected_effect: str
    priority: Literal["P1", "P2", "P3"] = "P2"
    horizon_days: int = Field(default=7, ge=1, le=90)


class AiCourseForecast(BaseModel):
    summary: str
    completion_forecast_7d: int = Field(ge=0, le=100)
    completion_forecast_14d: int = Field(ge=0, le=100)
    completion_forecast_30d: int = Field(ge=0, le=100)
    average_progress_forecast_14d: int = Field(ge=0, le=100)
    high_risk_share_forecast_14d: int = Field(ge=0, le=100)
    key_actions: list[AiGroupAction] = Field(default_factory=list)


class AiStudentForecast(BaseModel):
    student_id: str
    student_name: str
    current_progress: int = Field(ge=0, le=100)
    predicted_progress_14d: int = Field(ge=0, le=100)
    predicted_progress_30d: int = Field(ge=0, le=100)
    risk_trend: Literal["up", "stable", "down"] = "stable"
    dropout_risk: Literal["low", "medium", "high"] = "low"
    main_factors: list[str] = Field(default_factory=list)
    recommended_actions_teacher: list[str] = Field(default_factory=list)


class AiInsightsMeta(BaseModel):
    confidence: int = Field(ge=0, le=100)
    assumptions: list[str] = Field(default_factory=list)


class AiEarlyRiskSignal(BaseModel):
    label: str
    value: int = Field(ge=0)
    threshold: int = Field(ge=0)
    severity: Literal["low", "medium", "high"] = "low"
    note: str


class AiInterventionTask(BaseModel):
    student_id: str | None = None
    student_name: str
    risk: Literal["low", "medium", "high"] = "medium"
    action: str
    eta_days: int = Field(default=7, ge=1, le=30)
    success_metric: str


class AiInterventionPlan(BaseModel):
    horizon_days: Literal[7, 14] = 14
    focus: str
    tasks: list[AiInterventionTask] = Field(default_factory=list)
    expected_outcome: str


class CourseAiInsightsResponse(BaseModel):
    course_forecast: AiCourseForecast
    student_forecasts: list[AiStudentForecast] = Field(default_factory=list)
    early_risk_signals: list[AiEarlyRiskSignal] = Field(default_factory=list)
    intervention_plan: AiInterventionPlan | None = None
    meta: AiInsightsMeta


class StudentAiInsightsResponse(BaseModel):
    summary: str
    risk_level: Literal["low", "medium", "high"] = "low"
    risk_score: int = Field(ge=0, le=100)
    predicted_progress_7d: int = Field(ge=0, le=100)
    predicted_progress_14d: int = Field(ge=0, le=100)
    predicted_progress_30d: int = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    focus_zones: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    cohort_comparison: str
    confidence: int = Field(ge=0, le=100)
    assumptions: list[str] = Field(default_factory=list)
