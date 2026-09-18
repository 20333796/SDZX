from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import ExternalResourceModel  # noqa: F401
from app.schemas import ExternalResourceCreate, ResourceCategory
from app.services.resources import create_resource


def test_resource_creation_rejects_unapproved_external_host() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    payload = ExternalResourceCreate(
        id="unapproved-resource",
        title="未批准资源",
        provider="外部平台",
        category=ResourceCategory.courses,
        course_level="本科",
        audience="测试学生",
        description="用于验证域名白名单。",
        url="https://example.invalid/course",
    )
    with Session(engine) as session:
        try:
            create_resource(session, payload)
        except ValueError as error:
            assert "allowlisted" in str(error)
        else:
            raise AssertionError("Unapproved external hosts must not be accepted")
