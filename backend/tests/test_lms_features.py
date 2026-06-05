from datetime import UTC, date, datetime, timedelta
import io
import zipfile

import pytest

from app.core.security.password import hash_password
from app.models.user import User, UserRole


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_and_login(
    client,
    *,
    email: str,
    role: str,
    first_name: str | None = None,
    second_name: str | None = None,
) -> dict:
    payload = {"email": email, "password": "strongpass123", "role": role}
    if first_name is not None:
        payload["first_name"] = first_name
    if second_name is not None:
        payload["second_name"] = second_name
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()


def create_admin(db_session) -> User:
    admin = User(
        email="admin@example.com",
        first_name="Admin",
        password_hash=hash_password("strongpass123"),
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


def login_admin(client) -> str:
    response = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "strongpass123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_user_profile_update_and_self_courses_flow(client):
    register_payload = register_and_login(client, email="student@example.com", role="student", first_name="Student")
    token = register_payload["access_token"]

    response = client.patch(
        "/api/v1/users/me",
        json={"first_name": "Updated", "second_name": "Student", "profile_photo_url": "https://cdn.example/avatar.png"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"
    assert response.json()["second_name"] == "Student"
    assert response.json()["profile_photo_url"] == "https://cdn.example/avatar.png"

    courses_response = client.get("/api/v1/users/me/courses", headers=auth_headers(token))
    assert courses_response.status_code == 200
    assert courses_response.json() == []


def test_user_profile_photo_upload(client):
    register_payload = register_and_login(client, email="upload@example.com", role="student", first_name="Uploader")
    token = register_payload["access_token"]

    response = client.post(
        "/api/v1/users/me/photo",
        headers=auth_headers(token),
        files={"file": ("avatar.png", b"\x89PNG\r\n\x1a\nfakepng", "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["profile_photo_url"]
    assert "/media/profile-photos/" in response.json()["profile_photo_url"]


def test_course_enrollment_module_comment_and_quiz_flow(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={
            "title": "FastAPI Basics",
            "description": "Course description",
            "thumbnail_url": "https://cdn.example/course.png",
            "is_free": True,
            "is_published": True,
        },
        headers=teacher_headers,
    )
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={
            "course_id": course_id,
            "title": "Intro module",
            "description": "Module description",
            "video_url": "https://cdn.example/video.mp4",
            "position": 1,
            "is_published": True,
        },
        headers=teacher_headers,
    )
    assert module_response.status_code == 201
    module_id = module_response.json()["id"]

    blocked_module = client.get(f"/api/v1/modules/{module_id}", headers=student_headers)
    assert blocked_module.status_code == 403

    enroll_response = client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)
    assert enroll_response.status_code == 201

    module_after_enroll = client.get(f"/api/v1/modules/{module_id}", headers=student_headers)
    assert module_after_enroll.status_code == 200

    comment_response = client.post(
        f"/api/v1/modules/{module_id}/comments",
        json={"content": "Great lesson"},
        headers=student_headers,
    )
    assert comment_response.status_code == 201
    assert comment_response.json()["user"]["email"] == "student@example.com"

    comments_response = client.get(f"/api/v1/modules/{module_id}/comments", headers=student_headers)
    assert comments_response.status_code == 200
    assert comments_response.json()[0]["content"] == "Great lesson"

    reply_response = client.post(
        f"/api/v1/modules/{module_id}/comments",
        json={"content": "Thanks for the feedback", "parent_comment_id": comment_response.json()["id"]},
        headers=teacher_headers,
    )
    assert reply_response.status_code == 201
    assert reply_response.json()["parent_comment_id"] == comment_response.json()["id"]

    comments_with_reply = client.get(f"/api/v1/modules/{module_id}/comments", headers=student_headers)
    assert comments_with_reply.status_code == 200
    assert comments_with_reply.json()[0]["replies"][0]["content"] == "Thanks for the feedback"

    quiz_response = client.post(
        f"/api/v1/modules/{module_id}/quiz",
        json={
            "title": "Intro quiz",
            "is_published": True,
            "questions": [
                {
                    "content": "What framework are we using?",
                    "options": ["FastAPI", "Django"],
                    "correct_option": "FastAPI",
                    "explanation": "The course is about FastAPI",
                    "position": 1,
                }
            ],
        },
        headers=teacher_headers,
    )
    assert quiz_response.status_code == 201
    quiz_id = quiz_response.json()["id"]

    get_quiz_response = client.get(f"/api/v1/quizzes/{quiz_id}", headers=student_headers)
    assert get_quiz_response.status_code == 200
    question_id = get_quiz_response.json()["questions"][0]["id"]

    submit_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/submit",
        json={"answers": [{"question_id": question_id, "selected_option": "FastAPI"}]},
        headers=student_headers,
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["score"] == 1
    assert submit_response.json()["results"][0]["is_correct"] is True

    attempts_response = client.get(f"/api/v1/quizzes/{quiz_id}/attempts/me", headers=student_headers)
    assert attempts_response.status_code == 200
    assert len(attempts_response.json()) == 1

    my_courses_response = client.get("/api/v1/users/me/courses", headers=student_headers)
    assert my_courses_response.status_code == 200
    assert my_courses_response.json()[0]["id"] == course_id


def test_student_cannot_create_course(client):
    student = register_and_login(client, email="student@example.com", role="student")
    response = client.post(
        "/api/v1/courses",
        json={"title": "Blocked", "description": "Nope"},
        headers=auth_headers(student["access_token"]),
    )
    assert response.status_code == 403


def test_teacher_can_list_and_remove_course_students(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", first_name="Student")
    other_teacher = register_and_login(client, email="other-teacher@example.com", role="teacher", first_name="Other Teacher")

    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])
    other_teacher_headers = auth_headers(other_teacher["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Managed course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]

    enroll_response = client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)
    assert enroll_response.status_code == 201

    students_response = client.get(f"/api/v1/courses/{course_id}/students", headers=teacher_headers)
    assert students_response.status_code == 200
    assert len(students_response.json()) == 1
    assert students_response.json()[0]["user"]["email"] == "student@example.com"

    forbidden_response = client.get(f"/api/v1/courses/{course_id}/students", headers=other_teacher_headers)
    assert forbidden_response.status_code == 403

    remove_response = client.delete(
        f"/api/v1/courses/{course_id}/students/{student['user']['id']}",
        headers=teacher_headers,
    )
    assert remove_response.status_code == 204

    students_after_remove = client.get(f"/api/v1/courses/{course_id}/students", headers=teacher_headers)
    assert students_after_remove.status_code == 200
    assert students_after_remove.json() == []


def test_teacher_course_students_include_progress(client):
    teacher = register_and_login(client, email="teacher-progress@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student-progress@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Teacher analytics course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Analytics module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert module_response.status_code == 201
    module_id = module_response.json()["id"]

    content_response = client.post(
        f"/api/v1/modules/{module_id}/contents/text",
        json={"title": "Theory", "text_content": "Lesson"},
        headers=teacher_headers,
    )
    assert content_response.status_code == 201
    content_id = content_response.json()["id"]

    assignment_response = client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={"title": "Homework", "instructions_markdown": "Do it", "max_score": 10, "is_published": True},
        headers=teacher_headers,
    )
    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]

    enroll_response = client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)
    assert enroll_response.status_code == 201

    client.post(f"/api/v1/module-contents/{content_id}/view", headers=student_headers)
    submission_response = client.post(
        f"/api/v1/assignments/{assignment_id}/submissions",
        headers=student_headers,
        data={"answer_markdown": "Done"},
    )
    assert submission_response.status_code == 201

    grade_response = client.patch(
        f"/api/v1/assignment-submissions/{submission_response.json()['id']}/grade",
        json={"score": 9, "feedback_markdown": "Checked"},
        headers=teacher_headers,
    )
    assert grade_response.status_code == 200

    students_response = client.get(f"/api/v1/courses/{course_id}/students", headers=teacher_headers)
    assert students_response.status_code == 200
    payload = students_response.json()
    assert len(payload) == 1
    assert payload[0]["user"]["email"] == "student-progress@example.com"
    assert payload[0]["progress"]["progress_percent"] == 100
    assert payload[0]["progress"]["viewed_contents"] == 1
    assert payload[0]["progress"]["completed_assignments"] == 1
    assert payload[0]["progress_status"] == "completed"
    assert payload[0]["last_activity_at"] is not None
    assert payload[0]["inactivity_days"] == 0
    assert payload[0]["pending_assignments_count"] == 0
    assert payload[0]["passed_quizzes_count"] == 0
    assert payload[0]["failed_quizzes_count"] == 0
    assert payload[0]["overdue_items_count"] == 0
    assert payload[0]["upcoming_deadlines_count"] == 0
    assert payload[0]["late_submissions_count"] == 0
    assert payload[0]["average_assignment_score_percent"] == 90
    assert payload[0]["average_quiz_score_percent"] is None
    assert payload[0]["recent_activity_count_7d"] >= 1
    assert payload[0]["recent_completed_items_7d"] >= 1
    assert payload[0]["engagement_trend"] == "stable"
    assert payload[0]["risk_score"] == 0
    assert payload[0]["risk_level"] == "low"

    csv_response = client.get(f"/api/v1/courses/{course_id}/students.csv", headers=teacher_headers)
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]
    csv_text = csv_response.text
    assert csv_text.startswith("\ufeff")
    assert "student_name;email;progress_percent;progress_status;completed_items;total_items" in csv_text
    assert "avg_assignment_score_percent;avg_quiz_score_percent;recent_activity_count_7d;recent_completed_items_7d;pseudo_activity;engagement_trend;last_activity_at" in csv_text
    assert len(csv_text.splitlines()) >= 2
    assert "student-progress@example.com" in csv_text

    analytics_response = client.get(f"/api/v1/courses/{course_id}/analytics.zip", headers=teacher_headers)
    assert analytics_response.status_code == 200
    assert analytics_response.headers["content-type"] == "application/zip"
    archive = zipfile.ZipFile(io.BytesIO(analytics_response.content))
    names = set(archive.namelist())
    assert {"course_summary.csv", "students_analytics.csv", "modules_analytics.csv"}.issubset(names)
    summary_csv = archive.read("course_summary.csv").decode("utf-8")
    students_csv = archive.read("students_analytics.csv").decode("utf-8")
    modules_csv = archive.read("modules_analytics.csv").decode("utf-8")
    assert "metric;value" in summary_csv
    assert "students_total" in summary_csv
    assert "student_name;email;progress_percent" in students_csv
    assert "module_id;module_title;student_count" in modules_csv


def test_teacher_course_students_include_risk_and_deadline_analytics(client):
    teacher = register_and_login(client, email="teacher-risk@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student-risk@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Risk analytics course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Risk analytics module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    module_id = module_response.json()["id"]

    overdue_due_at = (datetime.now(UTC) - timedelta(days=2)).isoformat()
    upcoming_due_at = (datetime.now(UTC) + timedelta(days=2)).isoformat()

    client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={
            "title": "Overdue homework",
            "instructions_markdown": "Do it",
            "max_score": 10,
            "due_at": overdue_due_at,
            "is_published": True,
        },
        headers=teacher_headers,
    )
    client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={
            "title": "Upcoming homework",
            "instructions_markdown": "Do it later",
            "max_score": 10,
            "due_at": upcoming_due_at,
            "is_published": True,
        },
        headers=teacher_headers,
    )
    quiz_response = client.post(
        f"/api/v1/modules/{module_id}/quiz",
        json={
            "title": "Risk quiz",
            "is_published": True,
            "questions": [
                {
                    "content": "What framework are we using?",
                    "options": ["FastAPI", "Django"],
                    "correct_option": "FastAPI",
                    "explanation": "FastAPI",
                    "position": 1,
                }
            ],
        },
        headers=teacher_headers,
    )
    quiz_id = quiz_response.json()["id"]
    question_id = quiz_response.json()["questions"][0]["id"]

    enroll_response = client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)
    assert enroll_response.status_code == 201

    failed_attempt = client.post(
        f"/api/v1/quizzes/{quiz_id}/submit",
        json={"answers": [{"question_id": question_id, "selected_option": "Django"}]},
        headers=student_headers,
    )
    assert failed_attempt.status_code == 200

    students_response = client.get(f"/api/v1/courses/{course_id}/students", headers=teacher_headers)
    assert students_response.status_code == 200
    payload = students_response.json()
    assert len(payload) == 1
    student_row = payload[0]
    assert student_row["overdue_items_count"] == 1
    assert student_row["upcoming_deadlines_count"] == 1
    assert student_row["failed_quizzes_count"] == 1
    assert student_row["average_assignment_score_percent"] is None
    assert student_row["average_quiz_score_percent"] == 0
    assert student_row["recent_activity_count_7d"] >= 1
    assert student_row["recent_completed_items_7d"] == 0
    assert student_row["engagement_trend"] in {"stable", "growing"}
    assert student_row["risk_score"] >= 40
    assert student_row["risk_level"] in {"medium", "high"}


def test_student_hidden_draft_course_disappears_from_my_courses(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Draftable course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]

    enroll_response = client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)
    assert enroll_response.status_code == 201

    my_courses_before = client.get("/api/v1/users/me/courses", headers=student_headers)
    assert my_courses_before.status_code == 200
    assert len(my_courses_before.json()) == 1

    draft_response = client.patch(
        f"/api/v1/courses/{course_id}",
        json={"is_published": False},
        headers=teacher_headers,
    )
    assert draft_response.status_code == 200

    my_courses_after = client.get("/api/v1/users/me/courses", headers=student_headers)
    assert my_courses_after.status_code == 200
    assert my_courses_after.json() == []


def test_module_positions_are_sequential_and_can_be_reordered(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", first_name="Teacher")
    teacher_headers = auth_headers(teacher["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Modules course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]

    first_module = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "First", "description": "First module", "is_published": True},
        headers=teacher_headers,
    )
    second_module = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Second", "description": "Second module", "is_published": True},
        headers=teacher_headers,
    )

    assert first_module.status_code == 201
    assert second_module.status_code == 201
    assert first_module.json()["position"] == 1
    assert second_module.json()["position"] == 2

    reorder_response = client.post(
        f"/api/v1/modules/course/{course_id}/reorder",
        json={"modules": [{"id": second_module.json()["id"]}, {"id": first_module.json()["id"]}]},
        headers=teacher_headers,
    )
    assert reorder_response.status_code == 200
    assert reorder_response.json()[0]["title"] == "Second"
    assert reorder_response.json()[0]["position"] == 1
    assert reorder_response.json()[1]["title"] == "First"
    assert reorder_response.json()[1]["position"] == 2


def test_module_contents_support_text_link_and_file(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Content course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Content module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert module_response.status_code == 201
    module_id = module_response.json()["id"]

    client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)

    text_response = client.post(
        f"/api/v1/modules/{module_id}/contents/text",
        json={"title": "Теория", "text_content": "Основной текст урока"},
        headers=teacher_headers,
    )
    assert text_response.status_code == 201
    assert text_response.json()["content_type"] == "text"

    link_response = client.post(
        f"/api/v1/modules/{module_id}/contents/link",
        json={"title": "Встроенный ресурс", "source_url": "https://example.com/embed"},
        headers=teacher_headers,
    )
    assert link_response.status_code == 201
    assert link_response.json()["content_type"] == "link"

    file_response = client.post(
        f"/api/v1/modules/{module_id}/contents/file",
        data={"title": "Конспект", "content_type": "pdf"},
        files={"file": ("lesson.pdf", b"%PDF-1.4 fake pdf", "application/pdf")},
        headers=teacher_headers,
    )
    assert file_response.status_code == 201
    assert file_response.json()["content_type"] == "pdf"
    assert "/media/module-assets/" in file_response.json()["asset_url"]

    contents_response = client.get(f"/api/v1/modules/{module_id}/contents", headers=student_headers)
    assert contents_response.status_code == 200
    assert [item["content_type"] for item in contents_response.json()] == ["text", "link", "pdf"]

    replace_response = client.post(
        f"/api/v1/module-contents/{file_response.json()['id']}/replace-file",
        data={"title": "Updated lesson handout"},
        files={"file": ("lesson-updated.pdf", b"%PDF-1.4 updated fake pdf", "application/pdf")},
        headers=teacher_headers,
    )
    assert replace_response.status_code == 200
    assert replace_response.json()["title"] == "Updated lesson handout"
    assert replace_response.json()["content_type"] == "pdf"
    assert replace_response.json()["asset_url"] != file_response.json()["asset_url"]


def test_module_contents_support_presentation_upload(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Presentation course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Presentation module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert module_response.status_code == 201
    module_id = module_response.json()["id"]

    client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)

    presentation_response = client.post(
        f"/api/v1/modules/{module_id}/contents/file",
        data={"title": "Слайды", "content_type": "presentation"},
        files={"file": ("slides.pptx", b"fake-pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
        headers=teacher_headers,
    )
    assert presentation_response.status_code == 201
    assert presentation_response.json()["content_type"] == "presentation"

    contents_response = client.get(f"/api/v1/modules/{module_id}/contents", headers=student_headers)
    assert contents_response.status_code == 200
    assert contents_response.json()[0]["content_type"] == "presentation"


def test_student_course_progress_tracks_content_assignment_and_quiz(client):
    teacher = register_and_login(client, email="progress-teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="progress-student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Progress course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Progress module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert module_response.status_code == 201
    module_id = module_response.json()["id"]

    content_response = client.post(
        f"/api/v1/modules/{module_id}/contents/text",
        json={"title": "Theory", "text_content": "Lesson body"},
        headers=teacher_headers,
    )
    assert content_response.status_code == 201
    content_id = content_response.json()["id"]

    assignment_response = client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={
            "title": "Homework",
            "instructions_markdown": "Do it",
            "max_score": 10,
            "is_published": True,
        },
        headers=teacher_headers,
    )
    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]

    quiz_response = client.post(
        f"/api/v1/modules/{module_id}/quiz",
        json={
            "title": "Progress quiz",
            "is_published": True,
            "questions": [
                {
                    "content": "What framework are we learning?",
                    "options": ["FastAPI", "Flask"],
                    "correct_option": "FastAPI",
                    "explanation": "This course uses FastAPI",
                    "position": 1,
                },
                {
                    "content": "Which database is used in the project?",
                    "options": ["PostgreSQL", "SQLite"],
                    "correct_option": "PostgreSQL",
                    "explanation": "The backend is configured for PostgreSQL",
                    "position": 2,
                }
            ],
        },
        headers=teacher_headers,
    )
    assert quiz_response.status_code == 201
    quiz_id = quiz_response.json()["id"]
    first_question_id = quiz_response.json()["questions"][0]["id"]
    second_question_id = quiz_response.json()["questions"][1]["id"]

    enroll_response = client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)
    assert enroll_response.status_code == 201

    initial_courses = client.get("/api/v1/users/me/courses", headers=student_headers)
    assert initial_courses.status_code == 200
    progress = initial_courses.json()[0]["progress"]
    assert progress["progress_percent"] == 0
    assert progress["total_items"] == 3
    assert progress["viewed_contents"] == 0
    assert progress["completed_assignments"] == 0
    assert progress["completed_quizzes"] == 0

    content_view_response = client.post(f"/api/v1/module-contents/{content_id}/view", headers=student_headers)
    assert content_view_response.status_code == 204

    after_content_view = client.get("/api/v1/users/me/courses", headers=student_headers)
    progress = after_content_view.json()[0]["progress"]
    assert progress["progress_percent"] == 20
    assert progress["viewed_contents"] == 1
    assert progress["completed_items"] == 1

    submission_response = client.post(
        f"/api/v1/assignments/{assignment_id}/submissions",
        headers=student_headers,
        data={"answer_markdown": "Done"},
    )
    assert submission_response.status_code == 201
    submission_id = submission_response.json()["id"]

    after_assignment = client.get("/api/v1/users/me/courses", headers=student_headers)
    progress = after_assignment.json()[0]["progress"]
    assert progress["progress_percent"] == 20
    assert progress["completed_assignments"] == 0
    assert progress["completed_items"] == 1

    grade_response = client.patch(
        f"/api/v1/assignment-submissions/{submission_id}/grade",
        json={"score": 8, "feedback_markdown": "Checked"},
        headers=teacher_headers,
    )
    assert grade_response.status_code == 200

    after_assignment_grade = client.get("/api/v1/users/me/courses", headers=student_headers)
    progress = after_assignment_grade.json()[0]["progress"]
    assert progress["progress_percent"] == 70
    assert progress["completed_assignments"] == 1
    assert progress["completed_items"] == 2

    quiz_submit_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/submit",
        json={
            "answers": [
                {"question_id": first_question_id, "selected_option": "FastAPI"},
                {"question_id": second_question_id, "selected_option": "SQLite"},
            ]
        },
        headers=student_headers,
    )
    assert quiz_submit_response.status_code == 200

    after_failed_quiz = client.get("/api/v1/users/me/courses", headers=student_headers)
    progress = after_failed_quiz.json()[0]["progress"]
    assert progress["progress_percent"] == 70
    assert progress["completed_quizzes"] == 0

    passed_quiz_submit_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/submit",
        json={
            "answers": [
                {"question_id": first_question_id, "selected_option": "FastAPI"},
                {"question_id": second_question_id, "selected_option": "PostgreSQL"},
            ]
        },
        headers=student_headers,
    )
    assert passed_quiz_submit_response.status_code == 200

    after_quiz = client.get("/api/v1/users/me/courses", headers=student_headers)
    progress = after_quiz.json()[0]["progress"]
    assert progress["progress_percent"] == 100
    assert progress["completed_quizzes"] == 1
    assert progress["completed_modules"] == 1
    assert progress["total_modules"] == 1
    assert after_quiz.json()[0]["progress_status"] == "completed"
    assert after_quiz.json()[0]["recent_completed_items_7d"] >= 2
    assert after_quiz.json()[0]["engagement_trend"] in {"stable", "growing"}


def test_reply_comment_must_belong_to_same_module(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Comments course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    course_id = course_response.json()["id"]

    first_module = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "First module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    second_module = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Second module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    first_module_id = first_module.json()["id"]
    second_module_id = second_module.json()["id"]

    client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)

    root_comment = client.post(
        f"/api/v1/modules/{first_module_id}/comments",
        json={"content": "Question about lesson"},
        headers=student_headers,
    )
    assert root_comment.status_code == 201

    wrong_reply = client.post(
        f"/api/v1/modules/{second_module_id}/comments",
        json={"content": "Reply", "parent_comment_id": root_comment.json()["id"]},
        headers=teacher_headers,
    )
    assert wrong_reply.status_code == 404


def test_comments_support_nested_replies(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Nested comments course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Nested module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    module_id = module_response.json()["id"]

    client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)

    root = client.post(
        f"/api/v1/modules/{module_id}/comments",
        json={"content": "Комментарий преподавателя"},
        headers=teacher_headers,
    )
    reply = client.post(
        f"/api/v1/modules/{module_id}/comments",
        json={"content": "Ответ студента", "parent_comment_id": root.json()["id"]},
        headers=student_headers,
    )
    nested_reply = client.post(
        f"/api/v1/modules/{module_id}/comments",
        json={"content": "Ответ преподавателя на ответ", "parent_comment_id": reply.json()["id"]},
        headers=teacher_headers,
    )

    assert root.status_code == 201
    assert reply.status_code == 201
    assert nested_reply.status_code == 201

    comments_response = client.get(f"/api/v1/modules/{module_id}/comments", headers=student_headers)
    assert comments_response.status_code == 200
    payload = comments_response.json()
    assert payload[0]["content"] == "Комментарий преподавателя"
    assert payload[0]["replies"][0]["content"] == "Ответ студента"
    assert payload[0]["replies"][0]["replies"][0]["content"] == "Ответ преподавателя на ответ"


def test_admin_analytics_counts_enrollments(client, db_session):
    create_admin(db_session)
    admin_token = login_admin(client)

    teacher = register_and_login(client, email="teacher@example.com", role="teacher")
    student = register_and_login(client, email="student@example.com", role="student")

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Analytics course", "description": "Desc", "is_published": True},
        headers=auth_headers(teacher["access_token"]),
    )
    course_id = course_response.json()["id"]
    client.post(f"/api/v1/courses/{course_id}/enroll", headers=auth_headers(student["access_token"]))

    overview_response = client.get("/api/v1/analytics/overview", headers=auth_headers(admin_token))
    assert overview_response.status_code == 200
    assert overview_response.json()["users"] == 3
    assert overview_response.json()["courses"] == 1
    assert overview_response.json()["enrollments"] == 1

    today = date.today().isoformat()
    daily_response = client.get(
        f"/api/v1/analytics/enrollments/daily?start_date={today}&end_date={today}",
        headers=auth_headers(admin_token),
    )
    assert daily_response.status_code == 200
    assert daily_response.json()[0]["enrollments"] == 1


def test_quiz_attempts_keep_latest_three_with_results(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Quiz attempts course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Quiz module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    module_id = module_response.json()["id"]

    client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)

    quiz_response = client.post(
        f"/api/v1/modules/{module_id}/quiz",
        json={
            "title": "Attempts quiz",
            "is_published": True,
            "questions": [
                {
                    "content": "What framework are we using?",
                    "options": ["FastAPI", "Django"],
                    "correct_option": "FastAPI",
                    "explanation": "The course is about FastAPI",
                    "position": 1,
                }
            ],
        },
        headers=teacher_headers,
    )
    quiz_id = quiz_response.json()["id"]
    question_id = quiz_response.json()["questions"][0]["id"]

    client.post(
        f"/api/v1/quizzes/{quiz_id}/submit",
        json={"answers": [{"question_id": question_id, "selected_option": "Django"}]},
        headers=student_headers,
    )
    client.post(
        f"/api/v1/quizzes/{quiz_id}/submit",
        json={"answers": [{"question_id": question_id, "selected_option": "FastAPI"}]},
        headers=student_headers,
    )
    client.post(
        f"/api/v1/quizzes/{quiz_id}/submit",
        json={"answers": [{"question_id": question_id, "selected_option": "Django"}]},
        headers=student_headers,
    )
    client.post(
        f"/api/v1/quizzes/{quiz_id}/submit",
        json={"answers": [{"question_id": question_id, "selected_option": "FastAPI"}]},
        headers=student_headers,
    )

    attempts_response = client.get(f"/api/v1/quizzes/{quiz_id}/attempts/me", headers=student_headers)
    assert attempts_response.status_code == 200
    attempts = attempts_response.json()
    assert len(attempts) == 3
    assert attempts[0]["score"] == 1
    assert attempts[0]["results"][0]["selected_option"] == "FastAPI"
    assert attempts[0]["results"][0]["is_correct"] is True


def test_assignments_and_quizzes_support_optional_deadlines_and_late_flags(client):
    teacher = register_and_login(client, email="deadline-teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="deadline-student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Deadline course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Deadline module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    module_id = module_response.json()["id"]

    enroll_response = client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)
    assert enroll_response.status_code == 201

    past_due_at = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    future_due_at = (datetime.now(UTC) + timedelta(days=3)).isoformat()

    assignment_response = client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={
            "title": "Deadline homework",
            "instructions_markdown": "Do it",
            "max_score": 10,
            "due_at": past_due_at,
            "is_published": True,
        },
        headers=teacher_headers,
    )
    assert assignment_response.status_code == 201
    assignment_payload = assignment_response.json()
    assignment_id = assignment_payload["id"]
    assert assignment_payload["due_at"] is not None

    no_deadline_assignment_response = client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={
            "title": "Optional deadline homework",
            "instructions_markdown": "Do it later",
            "max_score": 10,
            "is_published": True,
        },
        headers=teacher_headers,
    )
    assert no_deadline_assignment_response.status_code == 201
    assert no_deadline_assignment_response.json()["due_at"] is None

    submission_response = client.post(
        f"/api/v1/assignments/{assignment_id}/submissions",
        headers=student_headers,
        data={"answer_markdown": "Late answer"},
    )
    assert submission_response.status_code == 201
    assert submission_response.json()["is_late"] is True

    quiz_response = client.post(
        f"/api/v1/modules/{module_id}/quiz",
        json={
            "title": "Deadline quiz",
            "due_at": future_due_at,
            "is_published": True,
            "questions": [
                {
                    "content": "What framework are we using?",
                    "options": ["FastAPI", "Django"],
                    "correct_option": "FastAPI",
                    "explanation": "The course is about FastAPI",
                    "position": 1,
                }
            ],
        },
        headers=teacher_headers,
    )
    assert quiz_response.status_code == 201
    quiz_payload = quiz_response.json()
    quiz_id = quiz_payload["id"]
    question_id = quiz_payload["questions"][0]["id"]
    assert quiz_payload["due_at"] is not None

    updated_quiz_response = client.patch(
        f"/api/v1/quizzes/{quiz_id}",
        json={
            "title": "Deadline quiz updated",
            "due_at": past_due_at,
            "is_published": True,
            "questions": [
                {
                    "content": "What framework are we using?",
                    "options": ["FastAPI", "Django"],
                    "correct_option": "FastAPI",
                    "explanation": "The course is about FastAPI",
                    "position": 1,
                }
            ],
        },
        headers=teacher_headers,
    )
    assert updated_quiz_response.status_code == 200
    assert updated_quiz_response.json()["due_at"] is not None

    submit_quiz_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/submit",
        json={"answers": [{"question_id": question_id, "selected_option": "FastAPI"}]},
        headers=student_headers,
    )
    assert submit_quiz_response.status_code == 200
    assert submit_quiz_response.json()["is_late"] is True

    attempts_response = client.get(f"/api/v1/quizzes/{quiz_id}/attempts/me", headers=student_headers)
    assert attempts_response.status_code == 200
    assert attempts_response.json()[0]["is_late"] is True


def test_in_app_notifications_cover_learning_events_and_risk_alerts(client):
    teacher = register_and_login(client, email="notify-teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="notify-student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Notifications course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Notifications module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    module_id = module_response.json()["id"]

    enroll_response = client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)
    assert enroll_response.status_code == 201

    announcement_response = client.post(
        f"/api/v1/modules/{module_id}/comments",
        json={"content": "Please review the new requirements before submitting work."},
        headers=teacher_headers,
    )
    assert announcement_response.status_code == 201

    comment_response = client.post(
        f"/api/v1/modules/{module_id}/comments",
        json={"content": "Student comment"},
        headers=student_headers,
    )
    assert comment_response.status_code == 201

    reply_response = client.post(
        f"/api/v1/modules/{module_id}/comments",
        json={"content": "Teacher reply", "parent_comment_id": comment_response.json()["id"]},
        headers=teacher_headers,
    )
    assert reply_response.status_code == 201

    initial_due_at = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    updated_due_at = (datetime.now(UTC) + timedelta(days=5)).isoformat()
    assignment_response = client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={
            "title": "Notify assignment",
            "instructions_markdown": "Do it",
            "max_score": 10,
            "is_published": True,
            "due_at": initial_due_at,
        },
        headers=teacher_headers,
    )
    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]

    second_assignment_response = client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={
            "title": "Backup assignment",
            "instructions_markdown": "Do it too",
            "max_score": 10,
            "is_published": True,
        },
        headers=teacher_headers,
    )
    assert second_assignment_response.status_code == 201

    overdue_assignment_response = client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={
            "title": "Missed assignment",
            "instructions_markdown": "This one is already overdue",
            "max_score": 10,
            "is_published": True,
            "due_at": (datetime.now(UTC) - timedelta(days=2)).isoformat(),
        },
        headers=teacher_headers,
    )
    assert overdue_assignment_response.status_code == 201

    updated_assignment_response = client.patch(
        f"/api/v1/assignments/{assignment_id}",
        json={"due_at": updated_due_at},
        headers=teacher_headers,
    )
    assert updated_assignment_response.status_code == 200

    submission_response = client.post(
        f"/api/v1/assignments/{assignment_id}/submissions",
        headers=student_headers,
        data={"answer_markdown": "My answer"},
    )
    assert submission_response.status_code == 201
    submission_id = submission_response.json()["id"]

    teacher_notifications = client.get("/api/v1/users/me/notifications", headers=teacher_headers)
    assert teacher_notifications.status_code == 200
    teacher_items = teacher_notifications.json()["items"]
    assert any(item["type"] == "assignment_submitted" for item in teacher_items)

    grade_response = client.patch(
        f"/api/v1/assignment-submissions/{submission_id}/grade",
        json={"score": 9, "feedback_markdown": "Strong work"},
        headers=teacher_headers,
    )
    assert grade_response.status_code == 200

    quiz_response = client.post(
        f"/api/v1/modules/{module_id}/quiz",
        json={
            "title": "Notify quiz",
            "is_published": True,
            "questions": [
                {
                    "content": "What framework are we using?",
                    "options": ["FastAPI", "Django"],
                    "correct_option": "FastAPI",
                    "explanation": "FastAPI",
                    "position": 1,
                }
            ],
        },
        headers=teacher_headers,
    )
    assert quiz_response.status_code == 201
    quiz_id = quiz_response.json()["id"]
    question_id = quiz_response.json()["questions"][0]["id"]

    failed_quiz_attempt = client.post(
        f"/api/v1/quizzes/{quiz_id}/submit",
        json={"answers": [{"question_id": question_id, "selected_option": "Django"}]},
        headers=student_headers,
    )
    assert failed_quiz_attempt.status_code == 200

    student_notifications = client.get("/api/v1/users/me/notifications", headers=student_headers)
    assert student_notifications.status_code == 200
    student_payload = student_notifications.json()
    student_items = student_payload["items"]
    student_types = {item["type"] for item in student_items}
    assert "comment_reply" in student_types
    assert "teacher_announcement" in student_types
    assert "assignment_published" in student_types
    assert "deadline_changed" in student_types
    assert "assignment_feedback" in student_types
    assert "quiz_published" in student_types
    assert "performance_risk" in student_types
    assert student_payload["unread_count"] >= 6

    first_notification_id = student_items[0]["id"]
    mark_read_response = client.post(f"/api/v1/users/me/notifications/{first_notification_id}/read", headers=student_headers)
    assert mark_read_response.status_code == 200
    assert mark_read_response.json()["is_read"] is True

    mark_all_response = client.post("/api/v1/users/me/notifications/read-all", headers=student_headers)
    assert mark_all_response.status_code == 204

    after_read_all = client.get("/api/v1/users/me/notifications", headers=student_headers)
    assert after_read_all.status_code == 200
    assert after_read_all.json()["unread_count"] == 0


def test_comment_can_be_deleted_only_by_owner(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Comment delete course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Comment module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    module_id = module_response.json()["id"]

    client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)

    comment_response = client.post(
        f"/api/v1/modules/{module_id}/comments",
        json={"content": "Student comment"},
        headers=student_headers,
    )
    comment_id = comment_response.json()["id"]

    forbidden_delete = client.delete(f"/api/v1/comments/{comment_id}", headers=teacher_headers)
    assert forbidden_delete.status_code == 403

    own_delete = client.delete(f"/api/v1/comments/{comment_id}", headers=student_headers)
    assert own_delete.status_code == 204

    comments_response = client.get(f"/api/v1/modules/{module_id}/comments", headers=student_headers)
    assert comments_response.status_code == 200
    assert comments_response.json() == []


def test_comment_with_replies_is_soft_deleted(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Soft delete comments", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Comment module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    module_id = module_response.json()["id"]

    client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)

    root_comment = client.post(
        f"/api/v1/modules/{module_id}/comments",
        json={"content": "Teacher root"},
        headers=teacher_headers,
    )
    reply_comment = client.post(
        f"/api/v1/modules/{module_id}/comments",
        json={"content": "Student reply", "parent_comment_id": root_comment.json()["id"]},
        headers=student_headers,
    )
    assert root_comment.status_code == 201
    assert reply_comment.status_code == 201

    delete_response = client.delete(f"/api/v1/comments/{root_comment.json()['id']}", headers=teacher_headers)
    assert delete_response.status_code == 204

    comments_response = client.get(f"/api/v1/modules/{module_id}/comments", headers=student_headers)
    assert comments_response.status_code == 200
    payload = comments_response.json()
    assert payload[0]["is_deleted"] is True
    assert payload[0]["content"] == "Сообщение удалено"
    assert payload[0]["replies"][0]["content"] == "Student reply"

    reply_to_deleted = client.post(
        f"/api/v1/modules/{module_id}/comments",
        json={"content": "Reply to deleted", "parent_comment_id": root_comment.json()["id"]},
        headers=student_headers,
    )
    assert reply_to_deleted.status_code == 409


def test_deleted_placeholder_is_removed_after_last_reply_is_deleted(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Comment cleanup course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Cleanup module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    module_id = module_response.json()["id"]

    client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)

    root_comment = client.post(
        f"/api/v1/modules/{module_id}/comments",
        json={"content": "Root comment"},
        headers=teacher_headers,
    )
    reply_comment = client.post(
        f"/api/v1/modules/{module_id}/comments",
        json={"content": "Reply comment", "parent_comment_id": root_comment.json()["id"]},
        headers=student_headers,
    )
    assert root_comment.status_code == 201
    assert reply_comment.status_code == 201

    delete_root = client.delete(f"/api/v1/comments/{root_comment.json()['id']}", headers=teacher_headers)
    assert delete_root.status_code == 204

    delete_reply = client.delete(f"/api/v1/comments/{reply_comment.json()['id']}", headers=student_headers)
    assert delete_reply.status_code == 204

    comments_response = client.get(f"/api/v1/modules/{module_id}/comments", headers=student_headers)
    assert comments_response.status_code == 200
    assert comments_response.json() == []


def test_module_content_can_be_updated_and_deleted(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", first_name="Teacher")
    teacher_headers = auth_headers(teacher["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Editable content course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Editable module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    module_id = module_response.json()["id"]

    content_response = client.post(
        f"/api/v1/modules/{module_id}/contents/text",
        json={"title": "Первый текст", "text_content": "Старый текст"},
        headers=teacher_headers,
    )
    assert content_response.status_code == 201
    content_id = content_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/module-contents/{content_id}",
        json={"title": "Обновленный текст", "text_content": "Новый текст"},
        headers=teacher_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Обновленный текст"
    assert update_response.json()["text_content"] == "Новый текст"

    delete_response = client.delete(f"/api/v1/module-contents/{content_id}", headers=teacher_headers)
    assert delete_response.status_code == 204

    contents_response = client.get(f"/api/v1/modules/{module_id}/contents", headers=teacher_headers)
    assert contents_response.status_code == 200
    assert contents_response.json() == []


def test_quiz_after_attempts_allows_only_metadata_update(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Protected quiz course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Protected quiz module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    module_id = module_response.json()["id"]

    client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)

    quiz_response = client.post(
        f"/api/v1/modules/{module_id}/quiz",
        json={
            "title": "Protected quiz",
            "is_published": True,
            "questions": [
                {
                    "content": "What framework are we using?",
                    "options": ["FastAPI", "Django"],
                    "correct_option": "FastAPI",
                    "explanation": "The course is about FastAPI",
                    "position": 1,
                }
            ],
        },
        headers=teacher_headers,
    )
    quiz_id = quiz_response.json()["id"]
    question_id = quiz_response.json()["questions"][0]["id"]

    client.post(
        f"/api/v1/quizzes/{quiz_id}/submit",
        json={"answers": [{"question_id": question_id, "selected_option": "FastAPI"}]},
        headers=student_headers,
    )

    update_response = client.patch(
        f"/api/v1/quizzes/{quiz_id}",
        json={
            "title": "Edited quiz",
            "is_published": False,
            "questions": [
                {
                    "content": "What framework are we using?",
                    "options": ["FastAPI", "Django"],
                    "correct_option": "FastAPI",
                    "explanation": "The course is about FastAPI",
                    "position": 1,
                }
            ],
        },
        headers=teacher_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Edited quiz"
    assert update_response.json()["is_published"] is False

    change_questions_response = client.patch(
        f"/api/v1/quizzes/{quiz_id}",
        json={
            "title": "Edited quiz",
            "is_published": False,
            "questions": [
                {
                    "content": "Edited question",
                    "options": ["FastAPI", "Django"],
                    "correct_option": "FastAPI",
                    "explanation": "Still FastAPI",
                    "position": 1,
                }
            ],
        },
        headers=teacher_headers,
    )
    assert change_questions_response.status_code == 409

    delete_response = client.delete(f"/api/v1/quizzes/{quiz_id}", headers=teacher_headers)
    assert delete_response.status_code == 409


@pytest.mark.skip(reason="Assignment submissions now use a single editable current answer instead of multiple attempts")
def test_assignments_support_attachments_attempts_and_grading(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Assignments course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Assignments module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert module_response.status_code == 201
    module_id = module_response.json()["id"]

    enroll_response = client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)
    assert enroll_response.status_code == 201

    assignment_response = client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={
            "title": "Итоговое задание",
            "instructions_markdown": "# Задание\n\nПодготовьте краткий разбор.",
            "max_score": 10,
            "is_published": True,
        },
        headers=teacher_headers,
    )
    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]
    assert assignment_response.json()["has_submissions"] is False

    attachment_response = client.post(
        f"/api/v1/assignments/{assignment_id}/attachment",
        headers=teacher_headers,
        files=[("files", ("task.pdf", b"%PDF-1.4 fake task", "application/pdf"))],
    )
    assert attachment_response.status_code == 200
    assert attachment_response.json()["attachments"][0]["file_url"]
    assert attachment_response.json()["attachments"][0]["file_name"] == "task.pdf"

    list_response = client.get(f"/api/v1/modules/{module_id}/assignments", headers=student_headers)
    assert list_response.status_code == 200
    assert list_response.json()[0]["title"] == "Итоговое задание"

    for index in range(4):
        submission_response = client.post(
            f"/api/v1/assignments/{assignment_id}/submissions",
            headers=student_headers,
            data={"answer_markdown": f"Попытка {index + 1}"},
            files=[("files", (f"answer-{index + 1}.zip", b"PKfake", "application/zip"))],
        )
        assert submission_response.status_code == 201
        assert submission_response.json()["attempt_number"] == index + 1

    my_submissions = client.get(f"/api/v1/assignments/{assignment_id}/submissions/me", headers=student_headers)
    assert my_submissions.status_code == 200
    payload = my_submissions.json()
    assert len(payload) == 3
    assert payload[0]["attempt_number"] == 4
    assert payload[2]["attempt_number"] == 2

    submissions_for_teacher = client.get(f"/api/v1/assignments/{assignment_id}/submissions", headers=teacher_headers)
    assert submissions_for_teacher.status_code == 200
    assert len(submissions_for_teacher.json()) == 3
    latest_submission_id = submissions_for_teacher.json()[0]["id"]

    grade_response = client.patch(
        f"/api/v1/assignment-submissions/{latest_submission_id}/grade",
        json={"score": 9, "feedback_markdown": "Хорошая работа, но можно подробнее."},
        headers=teacher_headers,
    )
    assert grade_response.status_code == 200
    assert grade_response.json()["status"] == "graded"
    assert grade_response.json()["score"] == 9

    teacher_cannot_submit = client.post(
        f"/api/v1/assignments/{assignment_id}/submissions",
        headers=teacher_headers,
        data={"answer_markdown": "Teacher answer"},
    )
    assert teacher_cannot_submit.status_code == 403


def test_assignments_support_single_submission_edit_delete_and_grading(client):
    teacher = register_and_login(client, email="teacher2@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="student2@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Assignments single course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]

    module_response = client.post(
        "/api/v1/modules",
        json={"course_id": course_id, "title": "Assignments single module", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert module_response.status_code == 201
    module_id = module_response.json()["id"]

    enroll_response = client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)
    assert enroll_response.status_code == 201

    assignment_response = client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={
            "title": "Итоговое задание",
            "instructions_markdown": "# Задание\n\nПодготовьте краткий разбор.",
            "max_score": 10,
            "is_published": True,
        },
        headers=teacher_headers,
    )
    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]

    submission_response = client.post(
        f"/api/v1/assignments/{assignment_id}/submissions",
        headers=student_headers,
        data={"answer_markdown": "Первая версия ответа"},
        files=[("files", ("answer-1.rar", b"RARfake", "application/x-rar-compressed"))],
    )
    assert submission_response.status_code == 201
    submission_id = submission_response.json()["id"]
    assert submission_response.json()["attempt_number"] == 1

    duplicate_submission = client.post(
        f"/api/v1/assignments/{assignment_id}/submissions",
        headers=student_headers,
        data={"answer_markdown": "Второй ответ"},
    )
    assert duplicate_submission.status_code == 409

    updated_submission = client.patch(
        f"/api/v1/assignment-submissions/{submission_id}",
        headers=student_headers,
        data={"answer_markdown": "Обновленный ответ"},
        files=[("files", ("answer-1.docx", b"docxfake", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))],
    )
    assert updated_submission.status_code == 200
    assert updated_submission.json()["answer_markdown"] == "Обновленный ответ"
    assert updated_submission.json()["attachments"][0]["file_name"] == "answer-1.docx"

    my_submissions = client.get(f"/api/v1/assignments/{assignment_id}/submissions/me", headers=student_headers)
    assert my_submissions.status_code == 200
    payload = my_submissions.json()
    assert len(payload) == 1
    assert payload[0]["id"] == submission_id
    assert payload[0]["answer_markdown"] == "Обновленный ответ"

    submissions_for_teacher = client.get(f"/api/v1/assignments/{assignment_id}/submissions", headers=teacher_headers)
    assert submissions_for_teacher.status_code == 200
    assert len(submissions_for_teacher.json()) == 1
    latest_submission_id = submissions_for_teacher.json()[0]["id"]

    grade_response = client.patch(
        f"/api/v1/assignment-submissions/{latest_submission_id}/grade",
        json={"score": 9, "feedback_markdown": "Хорошая работа, но можно подробнее."},
        headers=teacher_headers,
    )
    assert grade_response.status_code == 200
    assert grade_response.json()["status"] == "graded"
    assert grade_response.json()["score"] == 9

    grade_reset_response = client.patch(
        f"/api/v1/assignment-submissions/{latest_submission_id}",
        headers=student_headers,
        data={"answer_markdown": "Финальная версия ответа"},
    )
    assert grade_reset_response.status_code == 200
    assert grade_reset_response.json()["status"] == "submitted"
    assert grade_reset_response.json()["score"] is None
    assert grade_reset_response.json()["feedback_markdown"] is None
    assert grade_reset_response.json()["graded_at"] is None

    forbidden_delete = client.delete(f"/api/v1/assignment-submissions/{latest_submission_id}", headers=teacher_headers)
    assert forbidden_delete.status_code == 403

    own_delete = client.delete(f"/api/v1/assignment-submissions/{latest_submission_id}", headers=student_headers)
    assert own_delete.status_code == 204

    my_submissions_after_delete = client.get(f"/api/v1/assignments/{assignment_id}/submissions/me", headers=student_headers)
    assert my_submissions_after_delete.status_code == 200
    assert my_submissions_after_delete.json() == []


def test_chat_supports_student_teacher_dialog_with_websocket_delivery(client):
    teacher = register_and_login(client, email="chat-teacher@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="chat-student@example.com", role="student", first_name="Student")
    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Chat course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]

    enroll_response = client.post(f"/api/v1/courses/{course_id}/enroll", headers=student_headers)
    assert enroll_response.status_code == 201

    student_conversations = client.get("/api/v1/chat/conversations", headers=student_headers)
    assert student_conversations.status_code == 200
    assert student_conversations.json()[0]["partner_id"] == teacher["user"]["id"]

    with client.websocket_connect(f"/api/v1/chat/ws?token={teacher['access_token']}") as teacher_ws:
        send_response = client.post(
            "/api/v1/chat/messages",
            json={"recipient_id": teacher["user"]["id"], "content": "Здравствуйте, можно уточнить дедлайн?"},
            headers=student_headers,
        )
        assert send_response.status_code == 201
        sent_message = send_response.json()
        assert sent_message["course_id"] == course_id
        assert sent_message["sender_id"] == student["user"]["id"]

        event = teacher_ws.receive_json()
        assert event["type"] == "chat.message"
        assert event["message"]["content"] == "Здравствуйте, можно уточнить дедлайн?"
        assert event["message"]["sender_id"] == student["user"]["id"]

    teacher_messages = client.get(f"/api/v1/chat/messages/{student['user']['id']}", headers=teacher_headers)
    assert teacher_messages.status_code == 200
    assert teacher_messages.json()[0]["content"] == "Здравствуйте, можно уточнить дедлайн?"

    teacher_notifications = client.get("/api/v1/users/me/notifications", headers=teacher_headers)
    assert teacher_notifications.status_code == 200
    assert teacher_notifications.json()["items"][0]["type"] == "chat_message"
    assert teacher_notifications.json()["items"][0]["link_url"] == f"/chat?partner={student['user']['id']}"

    mark_read_response = client.post(f"/api/v1/chat/messages/{student['user']['id']}/read", headers=teacher_headers)
    assert mark_read_response.status_code == 204

    updated_student_conversations = client.get("/api/v1/chat/conversations", headers=student_headers)
    assert updated_student_conversations.status_code == 200
    assert updated_student_conversations.json()[0]["last_message"] == "Здравствуйте, можно уточнить дедлайн?"


def test_chat_is_available_only_between_connected_course_participants(client):
    teacher = register_and_login(client, email="chat-owner@example.com", role="teacher", first_name="Teacher")
    student = register_and_login(client, email="chat-member@example.com", role="student", first_name="Student")
    stranger = register_and_login(client, email="chat-stranger@example.com", role="teacher", first_name="Stranger")

    teacher_headers = auth_headers(teacher["access_token"])
    student_headers = auth_headers(student["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        json={"title": "Access course", "description": "Desc", "is_published": True},
        headers=teacher_headers,
    )
    assert course_response.status_code == 201

    enroll_response = client.post(f"/api/v1/courses/{course_response.json()['id']}/enroll", headers=student_headers)
    assert enroll_response.status_code == 201

    forbidden_message = client.post(
        "/api/v1/chat/messages",
        json={"recipient_id": stranger["user"]["id"], "content": "Пишу вне курса"},
        headers=student_headers,
    )
    assert forbidden_message.status_code == 403

