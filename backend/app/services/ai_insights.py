import json
from datetime import UTC, datetime
from urllib import request, error
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db.session import get_db
from app.lib.user_name import get_user_display_name
from app.models.course import Course
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.module import ModuleRepository
from app.schemas.ai_insights import (
    AiEarlyRiskSignal,
    AiInterventionPlan,
    AiInterventionTask,
    AiStudentForecast,
    CourseAiInsightsResponse,
    StudentAiInsightsResponse,
)
from app.schemas.user import UserRead
from app.services.progress import ProgressService, get_progress_service


class AiInsightsService:
    def __init__(self, db: Session, progress: ProgressService) -> None:
        self.db = db
        self.progress = progress
        self.enrollments = EnrollmentRepository(db)
        self.modules = ModuleRepository(db)

    def generate_course_insights(
        self,
        *,
        course: Course,
        current_user: UserRead,
        students_limit: int = 15,
    ) -> CourseAiInsightsResponse:
        enrollments = self.enrollments.list_by_course(course.id)
        modules = [module for module in self.modules.list_by_course(course.id) if module.is_published]
        student_records: list[dict] = []
        module_map: dict[str, dict] = {}

        for enrollment in enrollments:
            student = UserRead.model_validate(enrollment.user)
            analytics = self.progress.build_student_course_analytics(course.id, student)
            p = analytics["progress"]
            student_records.append(
                {
                    "student_id": str(student.id),
                    "student_name": get_user_display_name(student),
                    "progress_percent": p.progress_percent,
                    "progress_status": analytics["progress_status"],
                    "risk_level": analytics["risk_level"],
                    "risk_score": analytics["risk_score"],
                    "inactivity_days": analytics["inactivity_days"] or 0,
                    "pending_assignments": analytics["pending_assignments_count"],
                    "failed_quizzes": analytics["failed_quizzes_count"],
                    "overdue_items": analytics["overdue_items_count"],
                    "upcoming_deadlines": analytics["upcoming_deadlines_count"],
                    "recent_activity_count_7d": analytics["recent_activity_count_7d"],
                    "recent_completed_items_7d": analytics["recent_completed_items_7d"],
                    "pseudo_activity": analytics["pseudo_activity"],
                    "engagement_trend": analytics["engagement_trend"],
                    "avg_assignment_score_percent": analytics["average_assignment_score_percent"],
                    "avg_quiz_score_percent": analytics["average_quiz_score_percent"],
                    "module_progress": [
                        {
                            "module_id": module.module_id,
                            "module_title": module.module_title,
                            "progress_percent": module.progress_percent,
                        }
                        for module in sorted(p.modules, key=lambda item: item.progress_percent)
                    ],
                    "weak_modules": [
                        module.module_title
                        for module in sorted(p.modules, key=lambda item: item.progress_percent)[:3]
                        if module.progress_percent < 70
                    ],
                }
            )

            for module in p.modules:
                item = module_map.get(module.module_id)
                if item is None:
                    item = {
                        "module_title": module.module_title,
                        "student_count": 0,
                        "sum_progress": 0,
                        "started": 0,
                        "completed": 0,
                    }
                    module_map[module.module_id] = item
                item["student_count"] += 1
                item["sum_progress"] += module.progress_percent
                if module.progress_percent > 0:
                    item["started"] += 1
                if module.progress_percent == 100:
                    item["completed"] += 1

        students_total = len(student_records)
        if students_total == 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No students enrolled in this course")

        avg_progress = round(sum(item["progress_percent"] for item in student_records) / students_total)
        high_risk = sum(1 for item in student_records if item["risk_level"] == "high")
        medium_risk = sum(1 for item in student_records if item["risk_level"] == "medium")
        stalled = sum(1 for item in student_records if item["engagement_trend"] == "stalled")
        pseudo = sum(1 for item in student_records if item["pseudo_activity"])
        overdue_total = sum(item["overdue_items"] for item in student_records)
        pending_total = sum(item["pending_assignments"] for item in student_records)

        module_analytics = []
        for module_id, item in module_map.items():
            count = item["student_count"] or 1
            module_analytics.append(
                {
                    "module_id": module_id,
                    "module_title": item["module_title"],
                    "avg_progress": round(item["sum_progress"] / count),
                    "start_rate": round((item["started"] / count) * 100),
                    "completion_rate": round((item["completed"] / count) * 100),
                }
            )
        module_analytics.sort(key=lambda x: x["avg_progress"])

        course_modules_context = []
        for module in modules[:20]:
            content_titles = [content.title for content in module.contents[:8]]
            assignment_titles = [assignment.title for assignment in module.assignments if assignment.is_published][:5]
            quiz_title = module.quiz.title if module.quiz is not None and module.quiz.is_published else None
            course_modules_context.append(
                {
                    "module_id": str(module.id),
                    "module_title": module.title,
                    "module_description": module.description,
                    "content_titles": content_titles,
                    "assignment_titles": assignment_titles,
                    "quiz_title": quiz_title,
                }
            )

        top_students_for_forecast = sorted(
            student_records,
            key=lambda x: (x["risk_score"], -x["overdue_items"], x["progress_percent"]),
            reverse=True,
        )[:students_limit]

        payload = {
            "course": {
                "id": str(course.id),
                "title": course.title,
                "category": course.category,
                "is_published": course.is_published,
            },
            "snapshot_at": datetime.now(UTC).isoformat(),
            "group_summary": {
                "students_total": students_total,
                "average_progress_percent": avg_progress,
                "high_risk_count": high_risk,
                "medium_risk_count": medium_risk,
                "stalled_count": stalled,
                "pseudo_activity_count": pseudo,
                "overdue_items_total": overdue_total,
                "pending_assignments_total": pending_total,
            },
            "course_modules_context": course_modules_context,
            "module_analytics": module_analytics[:12],
            "students_for_forecast": top_students_for_forecast,
        }

        system_prompt = """
Ты senior-аналитик образовательной платформы. Отвечай ТОЛЬКО валидным JSON (без markdown/пояснений).

Цель:
1) Дать подробный прогноз по курсу/группе.
2) Дать прогнозы по студентам.
3) Дать практические рекомендации преподавателю.

Ключевые правила:
- Не выдумывай данные: используй только факты из входного JSON.
- Обязательно опирайся на course_modules_context и module_analytics.
- Не давай общих советов вида "выполнить задания" без привязки к модулю/теме.
- Если данных мало, явно укажи это в meta.assumptions и снизь confidence.
- Будь конкретным: рекомендации должны быть исполнимыми и измеримыми.
- Учитывай псевдоактивность (много входов при низком прогрессе) как отдельный риск.
- Учитывай стагнацию, просрочки, низкие оценки и динамику активности 7d.
- Прогнозы делай консервативно, без "магических" скачков.

Требования к полям:
- course_forecast.summary:
  Короткий, но содержательный обзор (3-6 предложений):
  текущее состояние группы, главные риски, сильные стороны, узкие места по модулям.
- completion_forecast_7d/14d/30d:
  Прогноз доли завершивших курс в %.
- average_progress_forecast_14d:
  Ожидаемый средний прогресс группы через 14 дней.
- high_risk_share_forecast_14d:
  Ожидаемая доля студентов высокого риска через 14 дней.
- key_actions:
  4-7 действий. Для каждого:
  action = что конкретно сделать (с явной ссылкой на модуль/тему из course_modules_context);
  why = на каких метриках основано;
  expected_effect = ожидаемый эффект;
  priority = P1/P2/P3;
  horizon_days = через сколько дней ждать эффект.

- student_forecasts:
  Верни прогнозы по переданным students_for_forecast (не пропускай без причины).
  Для каждого студента:
  - main_factors: 3-6 конкретных факторов риска/потенциала.
  - recommended_actions_teacher: 3-6 точечных действий преподавателя с привязкой к модулю/теме/заданию.
  - risk_trend и dropout_risk должны быть согласованы с метриками.
  - Нельзя копировать один и тот же текст между студентами: рекомендации должны отличаться
    в зависимости от progress_percent, weak_modules и module_progress конкретного студента.
  - Минимум 2 рекомендации должны содержать явное название модуля из weak_modules.

- meta:
  confidence = 0..100;
  assumptions = 2-6 допущений/ограничений анализа.

Строгая JSON-схема ответа:
{
  "course_forecast": {
    "summary": "string",
    "completion_forecast_7d": 0,
    "completion_forecast_14d": 0,
    "completion_forecast_30d": 0,
    "average_progress_forecast_14d": 0,
    "high_risk_share_forecast_14d": 0,
    "key_actions": [
      {
        "action": "string",
        "why": "string",
        "expected_effect": "string",
        "priority": "P1",
        "horizon_days": 7
      }
    ]
  },
  "student_forecasts": [
    {
      "student_id": "string",
      "student_name": "string",
      "current_progress": 0,
      "predicted_progress_14d": 0,
      "predicted_progress_30d": 0,
      "risk_trend": "stable",
      "dropout_risk": "low",
      "main_factors": ["string"],
      "recommended_actions_teacher": ["string"]
    }
  ],
  "early_risk_signals": [
    {
      "label": "string",
      "value": 0,
      "threshold": 0,
      "severity": "low",
      "note": "string"
    }
  ],
  "intervention_plan": {
    "horizon_days": 14,
    "focus": "string",
    "tasks": [
      {
        "student_id": "string",
        "student_name": "string",
        "risk": "medium",
        "action": "string",
        "eta_days": 7,
        "success_metric": "string"
      }
    ],
    "expected_outcome": "string"
  },
  "meta": {
    "confidence": 0,
    "assumptions": ["string"]
  }
}
"""
        user_prompt = json.dumps(payload, ensure_ascii=False)

        raw = self._chat_completion(system_prompt=system_prompt, user_prompt=user_prompt)
        try:
            data = json.loads(raw)
            data = self._normalize_course_ai_payload(data)
            parsed = CourseAiInsightsResponse.model_validate(data)
            return self._enrich_course_ai(parsed, payload)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"LLM returned invalid JSON: {exc}",
            ) from exc

    def _enrich_course_ai(self, parsed: CourseAiInsightsResponse, source_payload: dict) -> CourseAiInsightsResponse:
        students = source_payload.get("students_for_forecast", [])
        summary = source_payload.get("group_summary", {})
        total = int(summary.get("students_total", 0) or 0)
        high_risk = int(summary.get("high_risk_count", 0) or 0)
        medium_risk = int(summary.get("medium_risk_count", 0) or 0)
        stalled = int(summary.get("stalled_count", 0) or 0)
        pseudo = int(summary.get("pseudo_activity_count", 0) or 0)
        overdue = int(summary.get("overdue_items_total", 0) or 0)

        if not parsed.early_risk_signals:
            parsed.early_risk_signals = [
                AiEarlyRiskSignal(
                    label="Высокий риск",
                    value=high_risk,
                    threshold=max(1, round(total * 0.15)),
                    severity="high" if high_risk >= max(1, round(total * 0.15)) else "medium",
                    note="Студенты с критичным риском требуют персонального контакта в первую очередь.",
                ),
                AiEarlyRiskSignal(
                    label="Стагнация",
                    value=stalled,
                    threshold=max(1, round(total * 0.2)),
                    severity="high" if stalled >= max(1, round(total * 0.25)) else "medium",
                    note="Нет видимого прогресса по учебным действиям за последнюю неделю.",
                ),
                AiEarlyRiskSignal(
                    label="Псевдоактивность",
                    value=pseudo,
                    threshold=max(1, round(total * 0.15)),
                    severity="medium" if pseudo >= max(1, round(total * 0.15)) else "low",
                    note="Есть просмотры контента, но почти нет продвижения по курсу.",
                ),
                AiEarlyRiskSignal(
                    label="Просрочки",
                    value=overdue,
                    threshold=max(1, total),
                    severity="high" if overdue > total else "medium" if overdue > 0 else "low",
                    note="Просроченные работы усиливают риск отставания и отчисления.",
                ),
            ]

        if parsed.intervention_plan is None:
            risky = [s for s in students if s.get("risk_level") in {"high", "medium"}]
            risky.sort(key=lambda s: (s.get("risk_score", 0), s.get("overdue_items", 0), s.get("inactivity_days", 0)), reverse=True)
            tasks: list[AiInterventionTask] = []
            for item in risky[:6]:
                risk_level = item.get("risk_level", "medium")
                eta = 3 if risk_level == "high" else 7
                weak_modules = [name for name in (item.get("weak_modules") or []) if name]
                module_hint = f" по модулю «{weak_modules[0]}»" if weak_modules else ""
                if int(item.get("failed_quizzes", 0) or 0) > 0:
                    action_text = (
                        f"Точечный разбор ошибок тестирования{module_hint} + мини-квиз из 5 вопросов "
                        "с повторной попыткой через 2-3 дня."
                    )
                    metric_text = "Рост результата теста до ≥70% и +5% к прогрессу за 7 дней."
                elif int(item.get("overdue_items", 0) or 0) > 0:
                    action_text = (
                        f"Антикризисный дедлайн-план{module_hint}: закрыть ближайшие просрочки в 72 часа "
                        "с одной контрольной точкой в чате."
                    )
                    metric_text = "Снижение просрочек до 0 и стабилизация риска в течение недели."
                elif int(item.get("pending_assignments", 0) or 0) > 0:
                    action_text = (
                        f"Ускорение сдачи работ{module_hint}: выдать шаблон ответа и чек-лист качества "
                        "для закрытия pending-заданий."
                    )
                    metric_text = "Снижение pending-заданий и +8-10% к прогрессу за 14 дней."
                else:
                    action_text = (
                        f"Персональный мини-план{module_hint} на 7 дней: 2 завершённых элемента и "
                        "короткий чек-ин по динамике."
                    )
                    metric_text = "Рост активности 7д и +10% к прогрессу за 14 дней."
                tasks.append(
                    AiInterventionTask(
                        student_id=item.get("student_id"),
                        student_name=item.get("student_name") or "Студент",
                        risk="high" if risk_level == "high" else "medium",
                        action=action_text,
                        eta_days=eta,
                        success_metric=metric_text,
                    )
                )
            if not tasks and students:
                first = students[0]
                tasks.append(
                    AiInterventionTask(
                        student_id=first.get("student_id"),
                        student_name=first.get("student_name") or "Студент",
                        risk="low",
                        action="Поддерживающий контакт и фиксация ближайшего дедлайна.",
                        eta_days=7,
                        success_metric="Сохранение темпа и отсутствие новых просрочек.",
                    )
                )
            parsed.intervention_plan = AiInterventionPlan(
                horizon_days=14,
                focus="Снижение доли high/medium risk через персональные короткие вмешательства.",
                tasks=tasks,
                expected_outcome=f"Снижение группы риска минимум на 10-20% и стабилизация темпа в течение 14 дней (high={high_risk}, medium={medium_risk}).",
            )

        self._personalize_student_forecasts(parsed, students)
        self._ensure_student_forecasts_completeness(parsed, students)
        self._sanitize_intervention_plan(parsed, students)
        return parsed

    def _personalize_student_forecasts(self, parsed: CourseAiInsightsResponse, students: list[dict]) -> None:
        if not parsed.student_forecasts:
            return

        by_id = {str(item.get("student_id")): item for item in students if item.get("student_id")}
        for forecast in parsed.student_forecasts:
            source = by_id.get(forecast.student_id)
            if source is None:
                continue

            weak_modules = [name for name in (source.get("weak_modules") or []) if name]
            existing_actions = list(forecast.recommended_actions_teacher or [])

            # Detect overly generic duplicate-like recommendations and enforce module-tied actions.
            joined = " ".join(existing_actions).lower()
            looks_generic = (
                len(existing_actions) < 3
                or ("выполн" in joined and "модул" not in joined)
                or len(set(action.strip().lower() for action in existing_actions if action.strip())) <= 1
            )

            personalized_actions = []
            for index, module_title in enumerate(weak_modules[:2], start=1):
                personalized_actions.append(
                    f"Модуль «{module_title}»: провести короткий разбор ключевых ошибок и назначить 1 контрольную задачу с проверкой через {2 + index} дня."
                )
            if int(source.get("failed_quizzes", 0) or 0) > 0 and weak_modules:
                personalized_actions.append(
                    f"По тестам в модуле «{weak_modules[0]}»: дать мини-тренировку из 5 вопросов и повторную попытку с целевым порогом ≥ 70%."
                )
            if int(source.get("pending_assignments", 0) or 0) > 0:
                personalized_actions.append(
                    "Зафиксировать дедлайн на ближайшие 48 часов по текущей работе и дать шаблон ответа, чтобы ускорить сдачу."
                )
            if int(source.get("inactivity_days", 0) or 0) >= 3:
                personalized_actions.append(
                    "Назначить персональный check-in в чате и согласовать микроплан на 7 дней (минимум 2 завершённых элемента)."
                )

            if looks_generic:
                forecast.recommended_actions_teacher = (personalized_actions or existing_actions)[:6]
            else:
                merged = existing_actions[:]
                for action in personalized_actions:
                    if action not in merged:
                        merged.append(action)
                forecast.recommended_actions_teacher = merged[:6]

    def _sanitize_intervention_plan(self, parsed: CourseAiInsightsResponse, students: list[dict]) -> None:
        plan = parsed.intervention_plan
        if plan is None:
            return

        by_id = {str(item.get("student_id")): item for item in students if item.get("student_id")}
        has_non_low_risk = any((item.get("risk_level") in {"high", "medium"}) for item in students)
        sanitized_tasks: list[AiInterventionTask] = []

        for task in plan.tasks:
            source = by_id.get(str(task.student_id)) if task.student_id else None
            if has_non_low_risk and source is not None and source.get("risk_level") == "low":
                # Low-risk students should not be in intervention plan while medium/high exist.
                continue

            if source is not None:
                weak_modules = [name for name in (source.get("weak_modules") or []) if name]
                if weak_modules and all(module_name not in task.action for module_name in weak_modules[:2]):
                    task.action = f"{task.action} Фокус: модуль «{weak_modules[0]}»."
                if source.get("risk_level") == "high":
                    task.risk = "high"
                elif source.get("risk_level") == "medium":
                    task.risk = "medium"
                else:
                    task.risk = "low"

            sanitized_tasks.append(task)

        if not sanitized_tasks and students:
            fallback = sorted(
                [item for item in students if item.get("risk_level") in {"high", "medium"}],
                key=lambda item: (item.get("risk_score", 0), item.get("overdue_items", 0)),
                reverse=True,
            )
            for item in fallback[:3]:
                weak_modules = [name for name in (item.get("weak_modules") or []) if name]
                module_hint = f" в модуле «{weak_modules[0]}»" if weak_modules else ""
                sanitized_tasks.append(
                    AiInterventionTask(
                        student_id=item.get("student_id"),
                        student_name=item.get("student_name") or "Студент",
                        risk="high" if item.get("risk_level") == "high" else "medium",
                        action=f"Персональный план вмешательства{module_hint} с контрольной точкой через 3 дня.",
                        eta_days=3 if item.get("risk_level") == "high" else 7,
                        success_metric="Снижение риска и рост прогресса минимум на 5-10%.",
                    )
                )

        plan.tasks = sanitized_tasks[:8]

    def _ensure_student_forecasts_completeness(self, parsed: CourseAiInsightsResponse, students: list[dict]) -> None:
        if not students:
            return

        existing_ids = {str(item.student_id) for item in (parsed.student_forecasts or [])}
        for source in students:
            student_id = str(source.get("student_id") or "")
            if not student_id or student_id in existing_ids:
                continue

            current_progress = int(source.get("progress_percent") or 0)
            risk_level = str(source.get("risk_level") or "low")
            weak_modules = [name for name in (source.get("weak_modules") or []) if name]
            module_hint = f" по модулю «{weak_modules[0]}»" if weak_modules else ""

            if risk_level == "high":
                risk_trend = "up"
                dropout_risk = "high"
                p14 = max(0, min(100, current_progress + 6))
                p30 = max(0, min(100, current_progress + 14))
            elif risk_level == "medium":
                risk_trend = "stable"
                dropout_risk = "medium"
                p14 = max(0, min(100, current_progress + 9))
                p30 = max(0, min(100, current_progress + 20))
            else:
                risk_trend = "down"
                dropout_risk = "low"
                p14 = max(0, min(100, current_progress + 12))
                p30 = max(0, min(100, current_progress + 24))

            parsed.student_forecasts.append(
                AiStudentForecast(
                    student_id=student_id,
                    student_name=source.get("student_name") or "Студент",
                    current_progress=current_progress,
                    predicted_progress_14d=p14,
                    predicted_progress_30d=p30,
                    risk_trend=risk_trend,
                    dropout_risk=dropout_risk,
                    main_factors=[
                        f"Текущий прогресс: {current_progress}%.",
                        f"Уровень риска: {risk_level} ({int(source.get('risk_score') or 0)}/100).",
                    ],
                    recommended_actions_teacher=[
                        f"Сфокусировать ближайшую работу{module_hint} и дать короткую контрольную точку в течение 3-5 дней.",
                        "Согласовать персональный план на 7 дней с измеримым результатом (прирост прогресса и/или снятие просрочек).",
                    ],
                )
            )

    def _normalize_course_ai_payload(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            return payload

        def to_int(value, default=0):
            try:
                return int(round(float(value)))
            except Exception:
                return default

        if "course_forecast" not in payload or not isinstance(payload.get("course_forecast"), dict):
            payload["course_forecast"] = {
                "summary": "Недостаточно данных для развернутого прогноза. Используйте текущие метрики курса.",
                "completion_forecast_7d": 0,
                "completion_forecast_14d": 0,
                "completion_forecast_30d": 0,
                "average_progress_forecast_14d": 0,
                "high_risk_share_forecast_14d": 0,
                "key_actions": [],
            }

        payload.setdefault("student_forecasts", [])
        payload.setdefault("early_risk_signals", [])

        if "meta" not in payload or not isinstance(payload.get("meta"), dict):
            payload["meta"] = {"confidence": 50, "assumptions": ["Ответ модели был частично неполным и дополнен дефолтами."]}

        course_forecast = payload.get("course_forecast")
        if isinstance(course_forecast, dict):
            course_forecast.setdefault("summary", "Сводка недоступна.")
            course_forecast.setdefault("completion_forecast_7d", 0)
            course_forecast.setdefault("completion_forecast_14d", 0)
            course_forecast.setdefault("completion_forecast_30d", 0)
            course_forecast.setdefault("average_progress_forecast_14d", 0)
            course_forecast.setdefault("high_risk_share_forecast_14d", 0)
            course_forecast.setdefault("key_actions", [])
            for field in [
                "completion_forecast_7d",
                "completion_forecast_14d",
                "completion_forecast_30d",
                "average_progress_forecast_14d",
                "high_risk_share_forecast_14d",
            ]:
                if field in course_forecast:
                    course_forecast[field] = max(0, min(100, to_int(course_forecast.get(field), 0)))
            for action in course_forecast.get("key_actions", []) or []:
                if isinstance(action, dict) and "horizon_days" in action:
                    action["horizon_days"] = max(1, min(90, to_int(action.get("horizon_days"), 7)))

        for student in payload.get("student_forecasts", []) or []:
            if not isinstance(student, dict):
                continue
            student.setdefault("student_id", "")
            student.setdefault("student_name", "Студент")
            student.setdefault("risk_trend", "stable")
            student.setdefault("dropout_risk", "low")
            student.setdefault("main_factors", [])
            student.setdefault("recommended_actions_teacher", [])
            for field in ["current_progress", "predicted_progress_14d", "predicted_progress_30d"]:
                if field in student:
                    student[field] = max(0, min(100, to_int(student.get(field), 0)))
                else:
                    student[field] = 0

        for signal in payload.get("early_risk_signals", []) or []:
            if not isinstance(signal, dict):
                continue
            if "value" in signal:
                signal["value"] = max(0, to_int(signal.get("value"), 0))
            if "threshold" in signal:
                signal["threshold"] = max(0, to_int(signal.get("threshold"), 0))

        intervention = payload.get("intervention_plan")
        if isinstance(intervention, dict):
            if "horizon_days" in intervention:
                intervention["horizon_days"] = 14 if to_int(intervention.get("horizon_days"), 14) >= 14 else 7
            for task in intervention.get("tasks", []) or []:
                if isinstance(task, dict) and "eta_days" in task:
                    task["eta_days"] = max(1, min(30, to_int(task.get("eta_days"), 7)))

        meta = payload.get("meta")
        if isinstance(meta, dict):
            meta.setdefault("assumptions", [])
            if not isinstance(meta.get("assumptions"), list):
                meta["assumptions"] = [str(meta.get("assumptions"))]
            meta["confidence"] = max(0, min(100, to_int(meta.get("confidence"), 50)))

        return payload

    def generate_student_insights(
        self,
        *,
        course: Course,
        current_user: UserRead,
    ) -> StudentAiInsightsResponse:
        analytics = self.progress.build_student_course_analytics(course.id, current_user)
        progress = analytics["progress"]
        modules = [module for module in self.modules.list_by_course(course.id) if module.is_published]

        enrollments = self.enrollments.list_by_course(course.id)
        cohort_progress_values: list[int] = []
        cohort_risk_values: list[int] = []
        for enrollment in enrollments:
            student = UserRead.model_validate(enrollment.user)
            student_analytics = self.progress.build_student_course_analytics(course.id, student)
            cohort_progress_values.append(student_analytics["progress"].progress_percent)
            cohort_risk_values.append(student_analytics["risk_score"])

        cohort_avg_progress = round(sum(cohort_progress_values) / len(cohort_progress_values)) if cohort_progress_values else 0
        cohort_avg_risk = round(sum(cohort_risk_values) / len(cohort_risk_values)) if cohort_risk_values else 0

        payload = {
            "course": {
                "id": str(course.id),
                "title": course.title,
                "category": course.category,
            },
            "snapshot_at": datetime.now(UTC).isoformat(),
            "student": {
                "id": str(current_user.id),
                "name": get_user_display_name(current_user),
                "progress_percent": progress.progress_percent,
                "progress_status": analytics["progress_status"],
                "completed_items": progress.completed_items,
                "total_items": progress.total_items,
                "completed_modules": progress.completed_modules,
                "total_modules": progress.total_modules,
                "viewed_contents": progress.viewed_contents,
                "total_contents": progress.total_contents,
                "risk_score": analytics["risk_score"],
                "risk_level": analytics["risk_level"],
                "inactivity_days": analytics["inactivity_days"] or 0,
                "pending_assignments": analytics["pending_assignments_count"],
                "failed_quizzes": analytics["failed_quizzes_count"],
                "overdue_items": analytics["overdue_items_count"],
                "upcoming_deadlines": analytics["upcoming_deadlines_count"],
                "recent_activity_count_7d": analytics["recent_activity_count_7d"],
                "recent_completed_items_7d": analytics["recent_completed_items_7d"],
                "pseudo_activity": analytics["pseudo_activity"],
                "engagement_trend": analytics["engagement_trend"],
                "avg_assignment_score_percent": analytics["average_assignment_score_percent"],
                "avg_quiz_score_percent": analytics["average_quiz_score_percent"],
            },
            "cohort": {
                "students_total": len(enrollments),
                "average_progress_percent": cohort_avg_progress,
                "average_risk_score": cohort_avg_risk,
            },
            "course_modules_context": [
                {
                    "module_id": str(module.id),
                    "module_title": module.title,
                    "module_description": module.description,
                    "content_titles": [content.title for content in module.contents[:8]],
                    "assignment_titles": [assignment.title for assignment in module.assignments if assignment.is_published][:5],
                    "quiz_title": module.quiz.title if module.quiz is not None and module.quiz.is_published else None,
                }
                for module in modules[:20]
            ],
        }

        system_prompt = """
Ты учебный AI-ассистент для студента. Верни только валидный JSON без markdown.
Дай персональный прогноз по курсу и практические рекомендации.
Не выдумывай факты, опирайся только на входные данные.
Обязательно учитывай course_modules_context: рекомендации должны быть по конкретным модулям/темам курса.

Требования:
- summary: 2-5 предложений про текущую ситуацию студента.
- predicted_progress_7d/14d/30d: реалистичный прогноз прогресса в процентах.
- strengths: 2-5 сильных сторон.
- focus_zones: 2-5 зон фокуса, где студент теряет темп (с упоминанием модулей/тем).
- recommended_actions: 4-8 конкретных действий на ближайшие 7-14 дней с явной привязкой к модулю/заданию/тесту.
- cohort_comparison: краткое сравнение с группой (по прогрессу/риску).
- confidence: 0..100.
- assumptions: 2-6 ограничений/допущений.

Строгая схема:
{
  "summary": "string",
  "risk_level": "low",
  "risk_score": 0,
  "predicted_progress_7d": 0,
  "predicted_progress_14d": 0,
  "predicted_progress_30d": 0,
  "strengths": ["string"],
  "focus_zones": ["string"],
  "recommended_actions": ["string"],
  "cohort_comparison": "string",
  "confidence": 0,
  "assumptions": ["string"]
}
"""
        user_prompt = json.dumps(payload, ensure_ascii=False)
        raw = self._chat_completion(system_prompt=system_prompt, user_prompt=user_prompt)
        try:
            data = json.loads(raw)
            return StudentAiInsightsResponse.model_validate(data)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"LLM returned invalid JSON: {exc}",
            ) from exc

    def _chat_completion(self, *, system_prompt: str, user_prompt: str) -> str:
        primary = (settings.llm_provider or "groq").lower()
        fallback_raw = (settings.llm_fallback_providers or "").strip()
        fallbacks = [item.strip().lower() for item in fallback_raw.split(",") if item.strip()]
        providers = []
        for item in [primary, *fallbacks]:
            if item not in providers:
                providers.append(item)

        last_error = "unknown error"
        for provider in providers:
            api_key, model, base_url = self._resolve_provider(provider)
            if not api_key:
                last_error = f"{provider.upper()} key is not configured"
                continue

            try:
                if provider == "groq":
                    return self._chat_completion_groq_sdk(api_key, model, system_prompt, user_prompt)
                return self._chat_completion_http(api_key, model, base_url, provider, system_prompt, user_prompt)
            except Exception as exc:
                last_error = str(exc)

        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=last_error)

    def _chat_completion_groq_sdk(self, api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
        try:
            from groq import Groq
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"GROQ SDK is not installed: {exc}",
            ) from exc

        try:
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_completion_tokens=1400,
                top_p=1,
                stream=False,
                response_format={"type": "json_object"},
            )
            content = completion.choices[0].message.content
            if not content:
                raise ValueError("empty content")
            return content
        except Exception as exc:
            text = str(exc)
            if "1010" in text:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=(
                        "GROQ access error 1010. Обычно это блокировка на стороне Cloudflare/аккаунта. "
                        "Проверь: корректность GROQ_API_KEY, отключи VPN/прокси, попробуй другой интернет/сеть, "
                        "и проверь ограничения аккаунта Groq."
                    ),
                ) from exc
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"GROQ SDK error: {exc}") from exc

    def _chat_completion_http(
        self,
        api_key: str,
        model: str,
        base_url: str,
        provider: str,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        body = {
            "model": model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }

        data = json.dumps(body).encode("utf-8")
        req = request.Request(
            url=f"{base_url.rstrip('/')}/chat/completions",
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with request.urlopen(req, timeout=45) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            return payload["choices"][0]["message"]["content"]
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"{provider.upper()} HTTP error: {detail}") from exc
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"{provider.upper()} request failed: {exc}") from exc

    def _resolve_provider(self, provider: str) -> tuple[str | None, str, str]:
        if provider == "groq":
            return settings.groq_api_key, settings.groq_model, settings.groq_base_url
        return settings.openai_api_key, settings.openai_model, settings.openai_base_url


def get_ai_insights_service(
    db: Session = Depends(get_db),
    progress: ProgressService = Depends(get_progress_service),
) -> AiInsightsService:
    return AiInsightsService(db, progress)
