from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.db.session import SessionLocal
from app.models.assignment import Assignment
from app.models.course import Course
from app.models.module import Module
from app.models.module_content import ModuleContent, ModuleContentType
from app.models.quiz import Question, Quiz


COURSE_TITLE = "Основы Golang"


def build_module_specs() -> list[dict]:
    return [
        {
            "title": "Структуры, методы и интерфейсы",
            "description": "Разбираем структуры, методы и полиморфизм через интерфейсы.",
            "contents": [
                {
                    "title": "Struct и методы",
                    "content_type": ModuleContentType.TEXT,
                    "text_content": (
                        "В этом материале вы изучите объявление структур, инициализацию, вложенные структуры "
                        "и методы с value/pointer receiver."
                    ),
                },
                {
                    "title": "Интерфейсы в Go",
                    "content_type": ModuleContentType.TEXT,
                    "text_content": (
                        "Покрываем неявную реализацию интерфейсов, композицию интерфейсов и типичные ошибки "
                        "при проектировании API."
                    ),
                },
                {
                    "title": "Практика: проектирование доменной модели",
                    "content_type": ModuleContentType.LINK,
                    "source_url": "https://go.dev/tour/methods/1",
                },
            ],
            "assignment": {
                "title": "Модель интернет-магазина на struct + interface",
                "instructions_markdown": (
                    "Реализуйте доменную модель: `Product`, `Order`, `PaymentMethod`.\n\n"
                    "Требования:\n"
                    "1. Использовать минимум 3 структуры и 2 интерфейса.\n"
                    "2. Показать методы с pointer receiver и value receiver.\n"
                    "3. Добавить короткое описание архитектурных решений."
                ),
                "max_score": 100,
                "due_days": 6,
            },
            "quiz": {
                "title": "Проверка: структуры и интерфейсы",
                "due_days": 7,
                "questions": [
                    {
                        "content": "Как в Go тип реализует интерфейс?",
                        "options": ["Через ключевое слово implements", "Неявно, если совпадает набор методов", "Через наследование"],
                        "correct_option": "Неявно, если совпадает набор методов",
                        "explanation": "В Go интерфейсы реализуются неявно.",
                    },
                    {
                        "content": "Когда чаще нужен pointer receiver?",
                        "options": ["Когда метод меняет состояние структуры", "Только для больших структур", "Никогда"],
                        "correct_option": "Когда метод меняет состояние структуры",
                        "explanation": "Pointer receiver нужен для изменения полей и избежания лишнего копирования.",
                    },
                ],
            },
        },
        {
            "title": "Ошибки, пакеты и тестирование",
            "description": "Учимся грамотно обрабатывать ошибки, структурировать код по пакетам и писать unit-тесты.",
            "contents": [
                {
                    "title": "Обработка ошибок в Go",
                    "content_type": ModuleContentType.TEXT,
                    "text_content": (
                        "Рассматриваем idiomatic error handling, wrapping (`fmt.Errorf` + `%w`), "
                        "`errors.Is` / `errors.As`."
                    ),
                },
                {
                    "title": "Организация проекта по пакетам",
                    "content_type": ModuleContentType.TEXT,
                    "text_content": (
                        "Как разделять `cmd`, `internal`, `pkg`, избегать циклических зависимостей "
                        "и поддерживать читаемую архитектуру."
                    ),
                },
                {
                    "title": "Быстрый старт с `go test`",
                    "content_type": ModuleContentType.LINK,
                    "source_url": "https://go.dev/doc/tutorial/add-a-test",
                },
            ],
            "assignment": {
                "title": "Сервис заказов с валидацией ошибок и тестами",
                "instructions_markdown": (
                    "Создайте пакет `orders` с функцией создания заказа и обработкой бизнес-ошибок.\n\n"
                    "Требования:\n"
                    "1. Реализовать минимум 3 пользовательские ошибки.\n"
                    "2. Добавить unit-тесты для позитивного и негативных сценариев.\n"
                    "3. Покрытие критичных веток решения."
                ),
                "max_score": 100,
                "due_days": 8,
            },
            "quiz": {
                "title": "Проверка: ошибки и тестирование",
                "due_days": 9,
                "questions": [
                    {
                        "content": "Для чего используется `errors.Is`?",
                        "options": ["Сравнение ошибок с учетом wrapping", "Проверка nil-указателя", "Логирование ошибок"],
                        "correct_option": "Сравнение ошибок с учетом wrapping",
                        "explanation": "Функция проверяет цепочку обернутых ошибок.",
                    },
                    {
                        "content": "Как запускаются тесты в пакете?",
                        "options": ["go run tests", "go test ./...", "go check"],
                        "correct_option": "go test ./...",
                        "explanation": "Стандартный способ запуска тестов.",
                    },
                ],
            },
        },
        {
            "title": "Горутины, каналы и конкурентность",
            "description": "Изучаем concurrency-модель Go: горутины, каналы, select и безопасную синхронизацию.",
            "contents": [
                {
                    "title": "Горутины и каналы",
                    "content_type": ModuleContentType.TEXT,
                    "text_content": (
                        "Разбираем запуск горутин, буферизированные/небуферизированные каналы, "
                        "паттерны producer-consumer."
                    ),
                },
                {
                    "title": "select, context и отмена операций",
                    "content_type": ModuleContentType.TEXT,
                    "text_content": (
                        "Покрываем `select`, таймауты, graceful shutdown, "
                        "управление жизненным циклом конкурентных задач."
                    ),
                },
                {
                    "title": "Практика concurrency",
                    "content_type": ModuleContentType.LINK,
                    "source_url": "https://go.dev/tour/concurrency/1",
                },
            ],
            "assignment": {
                "title": "Параллельный обработчик задач",
                "instructions_markdown": (
                    "Реализуйте worker pool на горутинах.\n\n"
                    "Требования:\n"
                    "1. Канал задач, канал результатов.\n"
                    "2. Корректное завершение и отсутствие утечек горутин.\n"
                    "3. Отчёт по производительности (кратко)."
                ),
                "max_score": 100,
                "due_days": 10,
            },
            "quiz": {
                "title": "Проверка: конкурентность в Go",
                "due_days": 11,
                "questions": [
                    {
                        "content": "Что делает оператор `select`?",
                        "options": ["Выбирает готовый канал из нескольких операций", "Сортирует сообщения в канале", "Останавливает все горутины"],
                        "correct_option": "Выбирает готовый канал из нескольких операций",
                        "explanation": "`select` позволяет реагировать на первую готовую коммуникацию.",
                    },
                    {
                        "content": "Какой пакет часто применяют для отмены долгих операций?",
                        "options": ["os/signal", "context", "sync/atomic"],
                        "correct_option": "context",
                        "explanation": "`context` используется для отмены и таймаутов.",
                    },
                ],
            },
        },
    ]


def main() -> None:
    with SessionLocal() as db:
        course = db.scalar(select(Course).where(Course.title == COURSE_TITLE))
        if course is None:
            raise SystemExit(f"Course not found by title: {COURSE_TITLE}")

        existing_titles = {module.title for module in course.modules}
        position = max((module.position for module in course.modules), default=0)
        created_modules = 0

        for module_spec in build_module_specs():
            if module_spec["title"] in existing_titles:
                print(f"Skip existing module: {module_spec['title']}")
                continue

            position += 1
            module = Module(
                course_id=course.id,
                title=module_spec["title"],
                description=module_spec["description"],
                position=position,
                is_published=True,
            )
            db.add(module)
            db.flush()

            for idx, content_spec in enumerate(module_spec["contents"], start=1):
                content = ModuleContent(
                    module_id=module.id,
                    title=content_spec["title"],
                    content_type=content_spec["content_type"],
                    position=idx,
                    text_content=content_spec.get("text_content"),
                    source_url=content_spec.get("source_url"),
                )
                db.add(content)

            now = datetime.now(UTC)
            assignment_spec = module_spec["assignment"]
            assignment = Assignment(
                module_id=module.id,
                title=assignment_spec["title"],
                instructions_markdown=assignment_spec["instructions_markdown"],
                max_score=assignment_spec["max_score"],
                due_at=now + timedelta(days=assignment_spec["due_days"]),
                is_published=True,
            )
            db.add(assignment)

            quiz_spec = module_spec["quiz"]
            quiz = Quiz(
                module_id=module.id,
                title=quiz_spec["title"],
                due_at=now + timedelta(days=quiz_spec["due_days"]),
                is_published=True,
            )
            db.add(quiz)
            db.flush()

            for q_idx, question_spec in enumerate(quiz_spec["questions"], start=1):
                question = Question(
                    quiz_id=quiz.id,
                    content=question_spec["content"],
                    options_json=question_spec["options"],
                    correct_option=question_spec["correct_option"],
                    explanation=question_spec["explanation"],
                    position=q_idx,
                )
                db.add(question)

            created_modules += 1
            print(f"Created module: {module.title}")

        db.commit()
        print(f"Done. Added {created_modules} modules to course '{course.title}'.")


if __name__ == "__main__":
    main()
