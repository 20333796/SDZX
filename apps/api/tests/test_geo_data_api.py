from fastapi.testclient import TestClient

from app.main import app


def test_geo_datasets_are_seeded_and_listed() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/geo-data/datasets")
        assert response.status_code == 200
        datasets = response.json()
        assert len(datasets) >= 10
        assert any(item["id"] == "songliao-borehole-wells" for item in datasets)
        for item in datasets:
            assert item["feature_count"] >= 1


def test_geo_datasets_filter_by_category() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/geo-data/datasets?category=geochemistry")
        assert response.status_code == 200
        datasets = response.json()
        assert {item["id"] for item in datasets} == {"ordos-surface-geochemistry", "hydrogeochemistry-samples"}


def test_geo_dataset_detail_includes_sample_features() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/geo-data/datasets/songliao-borehole-wells")
        assert response.status_code == 200
        detail = response.json()
        assert detail["title"] == "松辽盆地公开钻孔位置目录"
        features = detail["features"]
        assert len(features) == 4
        first = features[0]
        assert 73 <= first["lon"] <= 136
        assert 3 <= first["lat"] <= 54
        assert first["name"]


def test_geo_dataset_detail_returns_404_for_unknown_id() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/geo-data/datasets/not-a-dataset").status_code == 404


def test_geo_dataset_stats_aggregates_categories_and_regions() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/geo-data/stats")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total"] >= 10
        assert stats["categories"] >= 6
        assert stats["regions"] >= 5
        assert stats["by_category"]["borehole"] == 1
        assert sum(stats["by_category"].values()) == stats["total"]


def test_geo_dataset_category_filter_rejects_unknown_value() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/geo-data/datasets?category=unknown").status_code == 422
