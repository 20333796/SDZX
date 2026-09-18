from fastapi.testclient import TestClient

from app.main import app


def test_course_knowledge_graph_has_nodes_and_relations() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/knowledge-graph")
        assert response.status_code == 200
        graph = response.json()
        assert len(graph["nodes"]) >= 30
        assert len(graph["edges"]) >= 45
        assert any(node["id"] == "well-log" for node in graph["nodes"])
        assert any(edge["target"] == "logging-interpretation" for edge in graph["edges"])
        assert {node["category"] for node in graph["nodes"]} == {"课程", "知识点", "能力"}


def test_knowledge_graph_filters_by_category_and_keeps_connected_edges() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/knowledge-graph?category=课程")
        assert response.status_code == 200
        graph = response.json()
        assert graph["nodes"]
        assert all(node["category"] == "课程" for node in graph["nodes"])
        node_ids = {node["id"] for node in graph["nodes"]}
        assert all(edge["source"] in node_ids and edge["target"] in node_ids for edge in graph["edges"])
        assert client.get("/api/v1/knowledge-graph?category=不存在").json()["nodes"] == []


def test_knowledge_graph_stats_aggregates_categories() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/knowledge-graph/stats")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total"] >= 30
        assert stats["relations"] >= 45
        assert sum(stats["by_category"].values()) == stats["total"]
        assert {"课程", "知识点", "能力"} <= set(stats["by_category"])


def test_knowledge_graph_node_detail_returns_neighbors() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/knowledge-graph/node/well-log")
        assert response.status_code == 200
        detail = response.json()
        assert detail["name"] == "地球物理测井"
        assert len(detail["neighbors"]) >= 5
        out = [n for n in detail["neighbors"] if n["direction"] == "out"]
        assert any(n["id"] == "logging-interpretation" and n["relation"] == "训练" for n in out)
        assert any(n["id"] == "well-log-advanced" and n["relation"] == "先修" for n in out)


def test_knowledge_graph_node_detail_exposes_both_directions() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/knowledge-graph/node/reservoir")
        assert response.status_code == 200
        neighbors = response.json()["neighbors"]
        into = [n for n in neighbors if n["direction"] == "in"]
        out = [n for n in neighbors if n["direction"] == "out"]
        assert any(n["id"] == "petroleum-geology" and n["relation"] == "讲授" for n in into)
        assert any(n["id"] == "reservoir-evaluation" and n["relation"] == "支撑" for n in out)


def test_knowledge_graph_node_detail_returns_404_for_unknown_id() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/knowledge-graph/node/not-a-node").status_code == 404
