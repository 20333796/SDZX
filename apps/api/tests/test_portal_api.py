from fastapi.testclient import TestClient

from app.main import app


def test_anonymous_portal_config_exposes_the_four_navigation_groups() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/portal-config")

    assert response.status_code == 200
    payload = response.json()
    assert [group["title"] for group in payload["navigation"]] == ["知源智汇", "因材智教", "实践智导", "能力智验"]
    assert payload["navigation"][0]["links"][0] == {
        "label": "AI智慧课程",
        "target": "resources",
        "category": "courses",
    }
    # 课程资源 = external_resources 真实计数，但有 45+ 展示下限（PORTAL_COURSE_STAT_FLOOR）；
    # 测试库资源数低于下限，因此固定断言 45+。
    assert payload["stats"] == [
        {"value": "45+", "label": "课程资源"},
        {"value": "03", "label": "学习路径"},
        {"value": "试运行", "label": "开放状态"},
    ]
