from datetime import date

import pytest

from app.core.security.password import hash_password
from app.models.user import User, UserRole


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_and_login(client, *, email: str, role: str, full_name: str | None = None) -> dict:
    payload = {"email": email, "password": "strongpass123", "role": role}
    if full_name is not None:
        payload["full_name"] = full_name
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()


def create_admin(db_session) -> User:
    admin = User(
        email="admin@example.com",
        full_name="Admin",
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
    register_payload = register_and_login(client, email="student@example.com", role="student", full_name="Student")
    token = register_payload["access_token"]

    response = client.patch(
        "/api/v1/users/me",
        json={"full_name": "Updated Student", "profile_photo_url": "https://cdn.example/avatar.png"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Student"
    assert response.json()["profile_photo_url"] == "https://cdn.example/avatar.png"

    courses_response = client.get("/api/v1/users/me/courses", headers=auth_headers(token))
    assert courses_response.status_code == 200
    assert courses_response.json() == []


def test_user_profile_photo_upload(client):
    register_payload = register_and_login(client, email="upload@example.com", role="student", full_name="Uploader")
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
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", full_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", full_name="Student")
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
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", full_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", full_name="Student")
    other_teacher = register_and_login(client, email="other-teacher@example.com", role="teacher", full_name="Other Teacher")

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


def test_student_hidden_draft_course_disappears_from_my_courses(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", full_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", full_name="Student")
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
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", full_name="Teacher")
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
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", full_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", full_name="Student")
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
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", full_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", full_name="Student")
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


def test_reply_comment_must_belong_to_same_module(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", full_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", full_name="Student")
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
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", full_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", full_name="Student")
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
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", full_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", full_name="Student")
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


def test_comment_can_be_deleted_only_by_owner(client):
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", full_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", full_name="Student")
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
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", full_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", full_name="Student")
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
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", full_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", full_name="Student")
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
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", full_name="Teacher")
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
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", full_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", full_name="Student")
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
    teacher = register_and_login(client, email="teacher@example.com", role="teacher", full_name="Teacher")
    student = register_and_login(client, email="student@example.com", role="student", full_name="Student")
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
    teacher = register_and_login(client, email="teacher2@example.com", role="teacher", full_name="Teacher")
    student = register_and_login(client, email="student2@example.com", role="student", full_name="Student")
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
