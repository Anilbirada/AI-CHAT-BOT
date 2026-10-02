import os

for stale in ("test_app.db", "test_app.db-journal"):
    if os.path.exists(stale):
        os.remove(stale)

os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_app.db")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("LLM_BASE_URL", "https://example.test/v1")
os.environ.setdefault("LLM_MODEL", "gpt-4o-mini")

from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app

client = TestClient(app)


def test_root_and_health():
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200


def test_register_and_login():
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "StrongPass123!",
        "role": "STUDENT",
    }

    reg = client.post("/api/auth/register", json=payload)
    assert reg.status_code == 200, reg.text
    assert "access_token" in reg.json()

    dup = client.post("/api/auth/register", json=payload)
    assert dup.status_code == 409

    login = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    assert token

    protected = client.get("/api/chats", headers={"Authorization": f"Bearer {token}"})
    assert protected.status_code == 200


def test_chat_requires_auth_and_saves_message():
    login = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "StrongPass123!"},
    )
    token = login.json()["access_token"]

    unauth = client.post("/api/chat", json={"message": "Hello"})
    assert unauth.status_code == 401

    with patch("app.services.llm_service.answer", return_value="Hello there! I am DSCE AI."):
        resp = client.post(
            "/api/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "Hello", "subject": "Computer Science", "semester": 4, "mode": "Simple Explanation"},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["answer"] == "Hello there! I am DSCE AI."
    assert body["conversation_id"] is not None

    history = client.get("/api/chats", headers={"Authorization": f"Bearer {token}"})
    assert history.status_code == 200
    assert len(history.json()) >= 1


def test_agent_handles_general_problem_without_mode_selection():
    login = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "StrongPass123!"},
    )
    token = login.json()["access_token"]

    with patch("app.services.llm_service.answer", return_value="Python is a general-purpose programming language."):
        resp = client.post(
            "/api/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "What is Python?", "subject": "Computer Science", "semester": 4, "mode": "General Problem Solving"},
        )

    assert resp.status_code == 200, resp.text
    assert "Python" in resp.json()["answer"]
    assert "intent" in resp.json()


def test_agent_streaming_endpoint_is_available():
    login = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "StrongPass123!"},
    )
    token = login.json()["access_token"]

    async def fake_stream(*args, **kwargs):
        yield "data: {\"choices\":[{\"delta\":{\"content\":\"Hi\"}}]}\n\n"
        yield "data: [DONE]\n\n"

    with patch("app.services.llm_service.stream_answer", fake_stream):
        resp = client.post(
            "/api/chat/stream",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "Explain SQL joins.", "subject": "Database", "semester": 4},
        )

    assert resp.status_code == 200, resp.text
    assert "text/event-stream" in resp.headers.get("content-type", "")
