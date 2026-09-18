import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.data_geo import GEO_DATASETS
from app.models import GeoDatasetModel
from app.schemas import GeoDataset, GeoDatasetCategory, GeoDatasetDetail, GeoDatasetFeature, GeoDatasetStats


def _to_detail(model: GeoDatasetModel, *, with_features: bool) -> GeoDatasetDetail | GeoDataset:
    features: list[GeoDatasetFeature] = []
    if with_features:
        raw = json.loads(model.features_json or "[]")
        features = [GeoDatasetFeature.model_validate(item) for item in raw]
    payload = {
        "id": model.id,
        "title": model.title,
        "category": model.category,
        "region": model.region,
        "description": model.description,
        "data_format": model.data_format,
        "resolution": model.resolution,
        "size_label": model.size_label,
        "source": model.source,
        "license": model.license,
        "access_url": model.access_url,
        "sort_order": model.sort_order,
        "feature_count": len(json.loads(model.features_json or "[]")),
    }
    if with_features:
        return GeoDatasetDetail(**payload, features=features)
    return GeoDataset(**payload)


def seed_geo_datasets(session: Session) -> None:
    if session.scalar(select(GeoDatasetModel.id).limit(1)):
        return
    for item in GEO_DATASETS:
        payload = {key: value for key, value in item.items() if key != "features"}
        features = item["features"]
        payload["category"] = payload["category"].value
        session.add(
            GeoDatasetModel(
                **payload,
                features_json=json.dumps(features, ensure_ascii=False),
            )
        )
    session.commit()


def list_geo_datasets(
    session: Session,
    category: GeoDatasetCategory | None = None,
) -> list[GeoDataset]:
    statement = select(GeoDatasetModel).order_by(GeoDatasetModel.sort_order, GeoDatasetModel.title)
    if category:
        statement = statement.where(GeoDatasetModel.category == category.value)
    return [_to_detail(model, with_features=False) for model in session.scalars(statement).all()]


def get_geo_dataset(session: Session, dataset_id: str) -> GeoDatasetModel | None:
    return session.get(GeoDatasetModel, dataset_id)


def dataset_stats(session: Session) -> GeoDatasetStats:
    rows = session.execute(
        select(GeoDatasetModel.category, func.count(GeoDatasetModel.id)).group_by(GeoDatasetModel.category)
    ).all()
    by_category = {category: count for category, count in rows}
    regions = session.scalar(select(func.count(func.distinct(GeoDatasetModel.region)))) or 0
    return GeoDatasetStats(
        total=sum(by_category.values()),
        categories=len(by_category),
        regions=int(regions),
        by_category=by_category,
    )
