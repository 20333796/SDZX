from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ResourceClickEvent
from app.schemas import ClickEvent, ExternalResource, ResourceCategory
from app.services.resources import get_resource, list_resources

router = APIRouter(prefix="/external-resources", tags=["external-resources"])


@router.get("", response_model=list[ExternalResource])
def get_resources(
    category: ResourceCategory | None = Query(default=None),
    provider: str | None = Query(default=None, max_length=255),
    course_level: str | None = Query(default=None, max_length=32),
    session: Session = Depends(get_db),
) -> list[ExternalResource]:
    return list_resources(session, category, provider, course_level)


@router.get("/{resource_id}", response_model=ExternalResource)
def get_resource_detail(resource_id: str, session: Session = Depends(get_db)) -> ExternalResource:
    resource = get_resource(session, resource_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return ExternalResource.model_validate(resource)


@router.post("/{resource_id}/click", status_code=status.HTTP_204_NO_CONTENT)
def track_resource_click(resource_id: str, payload: ClickEvent, response: Response, session: Session = Depends(get_db)) -> None:
    if not get_resource(session, resource_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    session.add(ResourceClickEvent(resource_id=resource_id, source=payload.source))
    session.commit()
    response.status_code = status.HTTP_204_NO_CONTENT

