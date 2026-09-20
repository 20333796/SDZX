from __future__ import annotations

import importlib
import socket

import ipaddress

import httpx
import pytest

router = importlib.import_module("server.routers.url_probe_router")


# =============================================================================
# === SSRF 护栏：validate_public_http_url ===
# =============================================================================


@pytest.mark.unit
def test_guard_rejects_non_http_schemes() -> None:
    for url in ("ftp://example.com", "file:///etc/passwd", "javascript:alert(1)", "gopher://x"):
        reason, _ips = router.validate_public_http_url(url)
        assert reason == "invalid-scheme", url


@pytest.mark.unit
def test_guard_rejects_missing_host() -> None:
    reason, _ips = router.validate_public_http_url("http:///path")
    assert reason == "invalid-url"


@pytest.mark.unit
def test_guard_rejects_dns_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_getaddrinfo(*_args, **_kwargs):
        raise socket.gaierror("no such host")

    monkeypatch.setattr(router.socket, "getaddrinfo", fake_getaddrinfo)
    reason, ips = router.validate_public_http_url("http://nonexistent.invalid")
    assert reason == "dns-failure"
    assert ips == []


@pytest.mark.unit
@pytest.mark.parametrize(
    "ip",
    [
        "10.1.2.3",
        "192.168.1.1",
        "172.16.0.9",
        "127.0.0.1",
        "169.254.3.4",
        "0.0.0.0",
        "::1",
        "fe80::1",
        "fc00::5",
    ],
)
def test_guard_rejects_private_and_reserved_ips(
    monkeypatch: pytest.MonkeyPatch, ip: str
) -> None:
    def fake_getaddrinfo(*_args, **_kwargs):
        return [(None, None, None, "", (ip, 0))]

    monkeypatch.setattr(router.socket, "getaddrinfo", fake_getaddrinfo)
    reason, ips = router.validate_public_http_url("http://host.example.com")
    assert reason == "intranet-or-reserved-ip"
    assert ips == [ip]


@pytest.mark.unit
def test_guard_rejects_mixed_public_private_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DNS rebinding 防护：多记录中只要有一条私网即拒绝。"""

    def fake_getaddrinfo(*_args, **_kwargs):
        return [
            (None, None, None, "", ("93.184.216.34", 0)),
            (None, None, None, "", ("10.0.0.5", 0)),
        ]

    monkeypatch.setattr(router.socket, "getaddrinfo", fake_getaddrinfo)
    reason, _ips = router.validate_public_http_url("http://rebind.example.com")
    assert reason == "intranet-or-reserved-ip"


@pytest.mark.unit
def test_guard_allows_fakeip_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    """宿主 Clash TUN fake-ip 环境：域名解析到 198.18.0.0/15 段必须放行。"""

    def fake_getaddrinfo(*_args, **_kwargs):
        return [(None, None, None, "", ("198.18.0.139", 0))]

    monkeypatch.setattr(router.socket, "getaddrinfo", fake_getaddrinfo)
    reason, ips = router.validate_public_http_url("https://example.com/")
    assert reason == ""
    assert ips == ["198.18.0.139"]


@pytest.mark.unit
def test_guard_allows_public_ip(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_getaddrinfo(*args, **_kwargs):
        host = args[0] if args else _kwargs.get("host")
        try:
            ipaddress.ip_address(host)
        except (ValueError, TypeError):
            return [(None, None, None, "", ("93.184.216.34", 0))]
        # IP 字面量原样返回，保留私网拦截语义
        return [(None, None, None, "", (host, 0))]

    monkeypatch.setattr(router.socket, "getaddrinfo", fake_getaddrinfo)
    reason, ips = router.validate_public_http_url("https://example.com/page")
    assert reason == ""
    assert ips == ["93.184.216.34"]


@pytest.mark.unit
def test_guard_rejects_literal_private_ip_url() -> None:
    """URL 直接写私网 IP（无 DNS）也必须拦截。"""
    reason, _ips = router.validate_public_http_url("http://192.168.1.10/admin")
    assert reason == "intranet-or-reserved-ip"


# =============================================================================
# === 判定逻辑：_judge_embeddable ===
# =============================================================================


def _headers(raw: dict[str, str] | None = None) -> httpx.Headers:
    return httpx.Headers(raw or {})


@pytest.mark.unit
@pytest.mark.parametrize("value", ["DENY", "SAMEORIGIN", "deny", " sameorigin "])
def test_judge_xfo_blocks(value: str) -> None:
    embeddable, why = router._judge_embeddable(_headers({"X-Frame-Options": value}))
    assert embeddable is False
    assert why.startswith("xfo-")


@pytest.mark.unit
@pytest.mark.parametrize(
    "csp",
    [
        "frame-ancestors 'none'",
        "default-src 'self'; frame-ancestors 'self'",
        "frame-ancestors https://trusted.example.com",
        "default-src *; frame-ancestors 'self' https://a.com",
    ],
)
def test_judge_csp_frame_ancestors_blocks(csp: str) -> None:
    embeddable, why = router._judge_embeddable(
        _headers({"Content-Security-Policy": csp})
    )
    assert embeddable is False
    assert why == "csp-frame-ancestors"


@pytest.mark.unit
@pytest.mark.parametrize(
    "csp",
    [
        "frame-ancestors *",
        "frame-ancestors http: https:",
        "default-src 'none'; frame-ancestors *",
    ],
)
def test_judge_csp_wildcard_allows(csp: str) -> None:
    embeddable, why = router._judge_embeddable(
        _headers({"Content-Security-Policy": csp})
    )
    assert embeddable is True
    assert why == "csp-wildcard"


@pytest.mark.unit
def test_judge_no_headers_allows() -> None:
    assert router._judge_embeddable(_headers({})) == (True, "no-embed-restriction")
    # 有 CSP 但无 frame-ancestors 指令：不影响嵌入
    embeddable, why = router._judge_embeddable(
        _headers({"Content-Security-Policy": "default-src 'self'"})
    )
    assert embeddable is True
    assert why == "no-embed-restriction"


@pytest.mark.unit
def test_judge_empty_frame_ancestors_treated_as_absent() -> None:
    embeddable, why = router._judge_embeddable(
        _headers({"Content-Security-Policy": "frame-ancestors"})
    )
    assert embeddable is True
    assert why == "no-embed-restriction"


# =============================================================================
# === 探测流程：_probe_url（MockTransport）===
# =============================================================================


def _client_with(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)


def _mock_public_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    """probe 类测试统一 mock DNS：护栏对测试域名解析为公网 IP（不依赖真实网络）。"""

    def fake_getaddrinfo(*args, **_kwargs):
        host = args[0] if args else _kwargs.get("host")
        try:
            ipaddress.ip_address(host)
        except (ValueError, TypeError):
            return [(None, None, None, "", ("93.184.216.34", 0))]
        # IP 字面量原样返回，保留私网拦截语义
        return [(None, None, None, "", (host, 0))]

    monkeypatch.setattr(router.socket, "getaddrinfo", fake_getaddrinfo)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_probe_direct_xfo_deny(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"X-Frame-Options": "DENY"})

    _mock_public_dns(monkeypatch)
    monkeypatch.setattr(router, "_build_probe_client", lambda: _client_with(handler))
    result = await router._probe_url("https://blocked.example.com/page")
    assert result == {"embeddable": False, "reason": "xfo-deny"}


@pytest.mark.asyncio
@pytest.mark.unit
async def test_probe_follows_redirects_and_judges_final(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if str(request.url).startswith("https://old.example.com"):
            return httpx.Response(
                301, headers={"Location": "https://new.example.com/final"}
            )
        return httpx.Response(200, headers={"Content-Security-Policy": "frame-ancestors *"})

    _mock_public_dns(monkeypatch)
    monkeypatch.setattr(router, "_build_probe_client", lambda: _client_with(handler))
    result = await router._probe_url("https://old.example.com/a")
    assert result == {"embeddable": True, "reason": "csp-wildcard"}
    assert calls == ["https://old.example.com/a", "https://new.example.com/final"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_probe_blocks_redirect_into_intranet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """重定向落点进内网（含私网 IP 直写）必须被逐跳护栏拦截。"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"Location": "http://192.168.1.5/panel"})

    _mock_public_dns(monkeypatch)
    monkeypatch.setattr(router, "_build_probe_client", lambda: _client_with(handler))
    result = await router._probe_url("https://evil-redirect.example.com/")
    assert result == {"embeddable": False, "reason": "intranet-or-reserved-ip"}


@pytest.mark.asyncio
@pytest.mark.unit
async def test_probe_too_many_redirects(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"Location": f"{request.url}/more"})

    _mock_public_dns(monkeypatch)
    monkeypatch.setattr(router, "_build_probe_client", lambda: _client_with(handler))
    result = await router._probe_url("https://loop.example.com/")
    assert result == {"embeddable": False, "reason": "too-many-redirects"}


@pytest.mark.asyncio
@pytest.mark.unit
async def test_probe_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out")

    _mock_public_dns(monkeypatch)
    monkeypatch.setattr(router, "_build_probe_client", lambda: _client_with(handler))
    result = await router._probe_url("https://slow.example.com/")
    assert result == {"embeddable": False, "reason": "timeout"}


# =============================================================================
# === 缓存与端点 ===
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
async def test_endpoint_caches_results(monkeypatch: pytest.MonkeyPatch) -> None:
    counter = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        counter["n"] += 1
        return httpx.Response(200)

    async def fake_probe(url: str) -> dict:
        handler(httpx.Request("GET", url))
        return {"embeddable": True, "reason": "no-embed-restriction"}

    router._EMBED_CHECK_CACHE.clear()
    monkeypatch.setattr(router, "_probe_url", fake_probe)

    first = await router.url_embed_check(url="https://cached.example.com/page", _current_user=None)
    second = await router.url_embed_check(url="https://cached.example.com/page#frag", _current_user=None)

    assert counter["n"] == 1
    assert first["cached"] is False
    assert second["cached"] is True
    # fragment 已归一化，两次指向同一缓存键
    assert first["checkedUrl"] == second["checkedUrl"]
    router._EMBED_CHECK_CACHE.clear()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_endpoint_probe_exception_falls_back_to_embeddable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def boom(url: str) -> dict:
        raise RuntimeError("unexpected")

    router._EMBED_CHECK_CACHE.clear()
    monkeypatch.setattr(router, "_probe_url", boom)
    result = await router.url_embed_check(url="https://broken.example.com/", _current_user=None)
    assert result["embeddable"] is True
    assert result["reason"] == "probe-error"
    router._EMBED_CHECK_CACHE.clear()
