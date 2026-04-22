from app.models.user import UserRole


def register_user(client, email="student@example.com", password="strongpass123", role="student"):
    response = client.post("/api/v1/auth/register", json={"email": email, "password": password, "role": role})
    assert response.status_code == 201
    return response.json()


def login_user(client, email="student@example.com", password="strongpass123"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_register_returns_tokens_and_student_role(client):
    data = register_user(client)

    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert data["user"]["role"] == UserRole.STUDENT


def test_register_duplicate_email_returns_409(client):
    register_user(client)

    response = client.post("/api/v1/auth/register", json={"email": "student@example.com", "password": "strongpass123"})

    assert response.status_code == 409


def test_login_returns_tokens(client):
    register_user(client)

    response = login_user(client)

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]


def test_register_teacher_role_for_frontend_testing(client):
    data = register_user(client, email="teacher@example.com", role="teacher")

    assert data["user"]["role"] == UserRole.TEACHER


def test_login_invalid_password_returns_401(client):
    register_user(client)

    response = client.post("/api/v1/auth/login", json={"email": "student@example.com", "password": "wrongpass123"})

    assert response.status_code == 401


def test_me_requires_valid_access_token(client):
    register_payload = register_user(client)
    token = register_payload["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "student@example.com"


def test_register_admin_role_is_rejected(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "password": "strongpass123", "role": "admin"},
    )

    assert response.status_code == 422
