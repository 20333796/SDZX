from fastapi.testclient import TestClient

from app.identity import Principal, Role, get_current_principal
from app.main import app


def test_diagnosis_overview_is_public_and_aggregated() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/learning/diagnosis/overview")
        assert response.status_code == 200
        overview = response.json()
        assert overview["tasks_total"] >= 3
        assert overview["submissions_total"] >= 6
        assert overview["reviewed_total"] >= 5
        assert overview["avg_score"] is not None
        assert len(overview["per_task"]) == overview["tasks_total"]
        assert sum(task["submissions"] for task in overview["per_task"]) == overview["submissions_total"]
        # 匿名聚合不携带学员身份
        assert "learner" not in str(overview).lower() or "demo-learner" not in str(overview)


def test_learner_diagnosis_requires_authentication() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/learning/diagnosis/demo-learner-01").status_code == 401


def test_learner_can_read_own_diagnosis_with_rule_based_output() -> None:
    principal = Principal(subject="demo-learner-01", name="演示学员", roles=frozenset({Role.learner}))
    app.dependency_overrides[get_current_principal] = lambda: principal
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/learning/diagnosis/demo-learner-01")
            assert response.status_code == 200
            report = response.json()
            assert report["learner_id"] == "demo-learner-01"
            assert report["attempts"] >= 2
            assert report["coverage"] > 0
            assert report["courses"]
            levels = {course["level"] for course in report["courses"]}
            assert levels <= {"扎实", "待巩固", "需加强"}
            assert report["suggestions"]
    finally:
        app.dependency_overrides.pop(get_current_principal)


def test_learner_cannot_read_someone_else_diagnosis() -> None:
    principal = Principal(subject="demo-learner-01", name="演示学员", roles=frozenset({Role.learner}))
    app.dependency_overrides[get_current_principal] = lambda: principal
    try:
        with TestClient(app) as client:
            assert client.get("/api/v1/learning/diagnosis/demo-learner-02").status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_principal)


def test_teacher_can_read_any_learner_diagnosis() -> None:
    principal = Principal(subject="teacher-01", name="演示教师", roles=frozenset({Role.teacher}))
    app.dependency_overrides[get_current_principal] = lambda: principal
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/learning/diagnosis/demo-learner-02")
            assert response.status_code == 200
            report = response.json()
            assert report["focus"], "低分学员应给出待加强项"
            assert report["strengths"] or report["courses"]
    finally:
        app.dependency_overrides.pop(get_current_principal)
