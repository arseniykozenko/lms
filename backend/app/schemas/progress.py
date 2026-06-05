from pydantic import BaseModel, Field


class ModuleProgressSummary(BaseModel):
    module_id: str
    module_title: str
    progress_percent: int = 0
    completed_items: int = 0
    total_items: int = 0


class CourseProgressSummary(BaseModel):
    progress_percent: int = 0
    completed_items: int = 0
    total_items: int = 0
    viewed_contents: int = 0
    total_contents: int = 0
    completed_assignments: int = 0
    total_assignments: int = 0
    completed_quizzes: int = 0
    total_quizzes: int = 0
    completed_modules: int = 0
    total_modules: int = 0
    modules: list[ModuleProgressSummary] = Field(default_factory=list)
