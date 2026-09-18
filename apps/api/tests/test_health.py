from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app import main


class UnavailableEngine:
    def connect(self):
        raise SQLAlchemyError("database unavailable")


def test_liveness_and_readiness_are_reported() -> None:
    with TestClient(main.app) as client:
        assert client.get("/healthz").json()["status"] == "ok"
        assert client.get("/readyz").json() == {"status": "ready", "database": "available"}


def test_readiness_rejects_traffic_when_database_is_unavailable(monkeypatch) -> None:
    with TestClient(main.app) as client:
        monkeypatch.setattr(main, "engine", UnavailableEngine())
        response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json()["detail"] == "Database is unavailable"
