from urllib.error import URLError

from app.schemas import ExternalResource, ResourceCategory, ResourceStatus
from app.services.resource_health import check_resource_link


class FakeResponse:
    def __init__(self, status: int, final_url: str) -> None:
        self.status = status
        self.final_url = final_url

    def geturl(self) -> str:
        return self.final_url


def resource(status: ResourceStatus = ResourceStatus.active, url: str | None = "https://higher.smartedu.cn/course/1") -> ExternalResource:
    return ExternalResource(
        id="resource-id",
        title="测试课程",
        provider="测试平台",
        category=ResourceCategory.courses,
        course_level="本科",
        audience="测试学生",
        status=status,
        url=url,
        description="测试资源。",
        sort_order=1,
    )


def test_pending_resource_is_not_requested() -> None:
    result = check_resource_link(resource(ResourceStatus.pending, None), {"higher.smartedu.cn"})
    assert result.outcome == "pending"


def test_active_resource_requires_allowlisted_host() -> None:
    result = check_resource_link(resource(url="https://example.invalid/course"), {"higher.smartedu.cn"})
    assert result.outcome == "invalid"


def test_platform_authorization_is_reported_without_being_marked_unavailable() -> None:
    def protected(*_args, **_kwargs):
        return FakeResponse(403, "https://higher.smartedu.cn/login")

    result = check_resource_link(resource(), {"higher.smartedu.cn"}, protected)
    assert result.outcome == "protected"
    assert result.status_code == 403


def test_network_failure_is_reported() -> None:
    def unavailable(*_args, **_kwargs):
        raise URLError("offline")

    result = check_resource_link(resource(), {"higher.smartedu.cn"}, unavailable)
    assert result.outcome == "failed"
