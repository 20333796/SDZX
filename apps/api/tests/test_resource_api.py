from fastapi.testclient import TestClient

from app.main import app


def test_resource_catalog_is_seeded_and_filterable() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/external-resources?category=practice")
        assert response.status_code == 200
        resources = response.json()
        assert any(resource["id"] == "radioactive-logging-vr" for resource in resources)
        response = client.get("/api/v1/external-resources?provider=智慧树&course_level=本科")
        assert response.status_code == 200
        assert [resource["id"] for resource in response.json()] == ["rock-forming-mineralogy"]


def test_click_event_accepts_anonymous_catalog_telemetry() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/external-resources/rock-forming-mineralogy/click",
            json={"source": "resource_catalog"},
        )
        assert response.status_code == 204


def test_oidc_protects_new_admin_and_knowledge_routes() -> None:
    with TestClient(app) as client:
        assert client.post("/api/v1/admin/external-resources", json={}).status_code == 401
        assert client.get("/api/v1/knowledge/documents").status_code == 401
        assert client.post("/api/v1/well-log/analyze-file").status_code == 401


def test_metrics_exposes_platform_request_counter() -> None:
    with TestClient(app) as client:
        client.get("/healthz")
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "deep_geology_http_requests_total" in response.text
