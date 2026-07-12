import os
from pathlib import Path

DB_PATH = Path("test_pc_builder.db")
DB_PATH.unlink(missing_ok=True)

os.environ.update(
    {
        "ENVIRONMENT": "test",
        "DATABASE_URL": "sqlite+aiosqlite:///./test_pc_builder.db",
        "REDIS_URL": "redis://localhost:6399/15",
        "AI_PROVIDER": "rules",
        "AUTO_CREATE_TABLES": "true",
        "SEED_DEMO_DATA": "true",
        "DEMO_EXPOSE_ONE_TIME_TOKENS": "true",
        "ADMIN_BOOTSTRAP_EMAIL": "admin@example.com",
        "ADMIN_BOOTSTRAP_PASSWORD": "Admin-password-123",
        "LOG_JSON": "false",
    }
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def clean_test_db():
    yield
    DB_PATH.unlink(missing_ok=True)


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def user_tokens(client):
    email = "user@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "display_name": "Test User", "password": "Strong-password-123"},
    )
    if response.status_code == 409:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Strong-password-123"},
        )
    assert response.status_code in {200, 201}, response.text
    return response.json()


@pytest.fixture
def auth_headers(user_tokens):
    return {"Authorization": f"Bearer {user_tokens['access_token']}"}


@pytest.fixture
def admin_headers(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Admin-password-123"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
