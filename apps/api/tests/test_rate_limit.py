from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_anonymous_chat_is_rate_limited(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "anonymous_chat_requests_per_minute", 2)
    with TestClient(app) as client:
        payload = {"mode": "conversation", "message": "测试限流"}
        assert client.post("/api/v1/chat/stream", json=payload).status_code == 200
        assert client.post("/api/v1/chat/stream", json=payload).status_code == 200
        assert client.post("/api/v1/chat/stream", json=payload).status_code == 429
