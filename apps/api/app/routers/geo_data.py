from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import GeoDataset, GeoDatasetCategory, GeoDatasetDetail, GeoDatasetStats
from app.services.geo_data import _to_detail, dataset_stats, get_geo_dataset, list_geo_datasets

router = APIRouter(prefix="/geo-data", tags=["geo-data"])


@router.get("/datasets", response_model=list[GeoDataset])
def get_geo_datasets(
    category: GeoDatasetCategory | None = Query(default=None),
    session: Session = Depends(get_db),
) -> list[GeoDataset]:
    return list_geo_datasets(session, category)


@router.get("/stats", response_model=GeoDatasetStats)
def get_geo_dataset_stats(session: Session = Depends(get_db)) -> GeoDatasetStats:
    return dataset_stats(session)


@router.get("/datasets/{dataset_id}", response_model=GeoDatasetDetail)
def get_geo_dataset_detail(dataset_id: str, session: Session = Depends(get_db)) -> GeoDatasetDetail:
    model = get_geo_dataset(session, dataset_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Geo dataset not found")
    detail = _to_detail(model, with_features=True)
    assert isinstance(detail, GeoDatasetDetail)
    return detail
