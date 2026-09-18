from fastapi.testclient import TestClient

from app.main import app


def test_learning_task_catalog_is_public_but_submission_requires_oidc() -> None:
    with TestClient(app) as client:
        catalog = client.get("/api/v1/learning/tasks")
        assert catalog.status_code == 200
        assert [task["id"] for task in catalog.json()] == [
            "petroleum-system-evidence",
            "well-log-reservoir-evidence",
            "exploration-target-synthesis",
        ]
        assert client.post(
            "/api/v1/learning/tasks/well-log-reservoir-evidence/submissions",
            json={"response": "教学回答"},
        ).status_code == 401
        assert client.get("/api/v1/learning/submissions/me").status_code == 401
