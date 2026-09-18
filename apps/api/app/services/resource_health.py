from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Iterable, Literal, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from app.config import get_settings
from app.schemas import ExternalResource, ResourceStatus


class OpenResponse(Protocol):
    status: int

    def geturl(self) -> str: ...


OpenRequest = Callable[[Request, float], OpenResponse]
HealthOutcome = Literal["healthy", "protected", "pending", "invalid", "failed"]


@dataclass(frozen=True)
class ResourceHealthResult:
    id: str
    title: str
    provider: str
    outcome: HealthOutcome
    url: str | None
    status_code: int | None
    final_url: str | None
    detail: str

    def to_dict(self) -> dict[str, str | int | None]:
        return asdict(self)


class AllowlistRedirectHandler(HTTPRedirectHandler):
    """Prevent release checks from following redirects outside approved platforms."""

    def __init__(self, allowed_hosts: set[str]) -> None:
        super().__init__()
        self.allowed_hosts = allowed_hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        host = urlparse(newurl).hostname
        if not host or host.lower() not in self.allowed_hosts:
            raise HTTPError(newurl, 403, "Redirect target is not allowlisted", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def build_open_request(allowed_hosts: set[str]) -> OpenRequest:
    opener = build_opener(AllowlistRedirectHandler(allowed_hosts))

    def open_request(request: Request, timeout: float) -> OpenResponse:
        return opener.open(request, timeout=timeout)

    return open_request


def check_resource_link(
    resource: ExternalResource,
    allowed_hosts: set[str],
    open_request: OpenRequest | None = None,
    timeout_seconds: float = 15,
) -> ResourceHealthResult:
    if resource.status == ResourceStatus.pending:
        return ResourceHealthResult(
            id=resource.id,
            title=resource.title,
            provider=resource.provider,
            outcome="pending",
            url=str(resource.url) if resource.url else None,
            status_code=None,
            final_url=None,
            detail="资源链接待学院补充。",
        )
    if not resource.url:
        return ResourceHealthResult(
            id=resource.id,
            title=resource.title,
            provider=resource.provider,
            outcome="invalid",
            url=None,
            status_code=None,
            final_url=None,
            detail="已发布资源缺少外部链接。",
        )

    url = str(resource.url)
    host = urlparse(url).hostname
    if not host or host.lower() not in allowed_hosts:
        return ResourceHealthResult(
            id=resource.id,
            title=resource.title,
            provider=resource.provider,
            outcome="invalid",
            url=url,
            status_code=None,
            final_url=None,
            detail="资源域名不在白名单中。",
        )

    try:
        response = (open_request or build_open_request(allowed_hosts))(
            Request(url, headers={"User-Agent": "DeepGeologyLinkCheck/1.0"}), timeout_seconds
        )
        status_code = response.status
        final_url = response.geturl()
    except HTTPError as error:
        status_code = error.code
        final_url = error.geturl()
    except URLError as error:
        return ResourceHealthResult(
            id=resource.id,
            title=resource.title,
            provider=resource.provider,
            outcome="failed",
            url=url,
            status_code=None,
            final_url=None,
            detail=f"连接失败：{error.reason}",
        )

    if status_code in {401, 403}:
        outcome: HealthOutcome = "protected"
        detail = "资源平台可达，需要统一认证或平台授权。"
    elif 200 <= status_code < 400:
        outcome = "healthy"
        detail = "资源链接可访问。"
    else:
        outcome = "failed"
        detail = f"资源平台返回 HTTP {status_code}。"
    return ResourceHealthResult(
        id=resource.id,
        title=resource.title,
        provider=resource.provider,
        outcome=outcome,
        url=url,
        status_code=status_code,
        final_url=final_url,
        detail=detail,
    )


def check_resource_links(
    resources: Iterable[ExternalResource],
    open_request: OpenRequest | None = None,
    timeout_seconds: float = 15,
) -> list[ResourceHealthResult]:
    allowed_hosts = get_settings().allowed_resource_hosts
    return [
        check_resource_link(resource, allowed_hosts, open_request, timeout_seconds)
        for resource in resources
    ]
