from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data import EXTERNAL_RESOURCES
from app.config import get_settings
from app.models import ExternalResourceModel
from app.schemas import ExternalResource, ExternalResourceCreate, ResourceCategory


def seed_resources(session: Session) -> None:
    if session.scalar(select(ExternalResourceModel.id).limit(1)):
        return
    seeded_resources = []
    for resource in EXTERNAL_RESOURCES:
        resource_data = resource.model_dump(mode="json", exclude_none=False)
        resource_data["category"] = resource.category.value
        resource_data["status"] = resource.status.value
        resource_data["url"] = str(resource.url) if resource.url else None
        seeded_resources.append(ExternalResourceModel(**resource_data))
    session.add_all(seeded_resources)
    session.commit()


def list_resources(
    session: Session,
    category: ResourceCategory | None = None,
    provider: str | None = None,
    course_level: str | None = None,
) -> list[ExternalResource]:
    statement = select(ExternalResourceModel).order_by(ExternalResourceModel.sort_order, ExternalResourceModel.title)
    if category:
        statement = statement.where(ExternalResourceModel.category == category.value)
    if provider:
        statement = statement.where(ExternalResourceModel.provider == provider)
    if course_level:
        statement = statement.where(ExternalResourceModel.course_level == course_level)
    return [ExternalResource.model_validate(resource) for resource in session.scalars(statement).all()]


def get_resource(session: Session, resource_id: str) -> ExternalResourceModel | None:
    return session.get(ExternalResourceModel, resource_id)


def create_resource(session: Session, payload: ExternalResourceCreate) -> ExternalResource:
    if payload.status.value == "active" and not payload.url:
        raise ValueError("Active resources require an external URL")
    if payload.url:
        host = urlparse(str(payload.url)).hostname
        if not host or host.lower() not in get_settings().allowed_resource_hosts:
            raise ValueError("External resource host is not allowlisted")
    resource_data = payload.model_dump(mode="json", exclude_none=False)
    resource_data["category"] = payload.category.value
    resource_data["status"] = payload.status.value
    resource_data["url"] = str(payload.url) if payload.url else None
    resource = ExternalResourceModel(**resource_data)
    session.add(resource)
    session.commit()
    session.refresh(resource)
    return ExternalResource.model_validate(resource)
