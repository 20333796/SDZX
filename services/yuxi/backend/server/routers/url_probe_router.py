"""URL 内嵌可行性预检（供「最近检索」面板等 iframe 打开外链前判定）。

依据目标站点的响应头（X-Frame-Options / CSP frame-ancestors）判断页面能否
被工作台跨站 iframe 嵌入。端点自带 SSRF 护栏：

- 仅允许 http/https scheme；
- 域名经 DNS 解析后，所有记录必须为公网地址（拒绝私有/回环/链路本地/保留段）；
- 重定向逐跳重新解析与校验（防 DNS rebinding / 跳转进内网）；
- 连接与总超时受限，仅读取响应头、不下载响应体；
- 结果进程内 TTL 缓存，避免对同一站点重复探测。
"""

import asyncio
import ipaddress
import socket
import time
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx
from fastapi import APIRouter, Depends, Query
from yuxi.utils.logging_config import logger

from server.utils.auth_middleware import get_required_user

url_probe = APIRouter(prefix="/tools", tags=["tools"])

_PROBE_TIMEOUT = httpx.Timeout(5.0, connect=3.0)
_MAX_REDIRECTS = 4
_CACHE_TTL_SECONDS = 300
_CACHE_MAX_ENTRIES = 512
_PROBE_USER_AGENT = "Mozilla/5.0 (compatible; YuxiEmbedProbe/1.0)"

# Clash/mihomo TUN fake-ip 基准段（借用 RFC 2544 保留段 198.18.0.0/15）。
# 该环境下所有域名都会解析到此段假地址，真实可达性由代理出口决定；
# 对这一段跳过 IP 归属校验（私网/回环等真实敏感段与 IP 字面量拦截不受影响）。
_FAKE_IP_NETWORK = ipaddress.ip_network("198.18.0.0/15")

# 进程内缓存：规范化 URL -> (monotonic 时间戳, 判定结果)
_EMBED_CHECK_CACHE: dict[str, tuple[float, dict]] = {}


def _normalize_url(url: str) -> str:
    """去掉 fragment 并补全空路径，作为缓存 key 与探测目标。"""
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))


def _is_blocked_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    if addr in _FAKE_IP_NETWORK:
        return False
    # is_global 排除私有、回环、链路本地、组播与 IETF 保留段
    return not addr.is_global


def validate_public_http_url(url: str) -> tuple[str, list[str]]:
    """SSRF 护栏：返回 (错误原因, 解析出的 IP 列表)，错误原因为空串表示通过。

    同步函数（内部走阻塞 DNS 解析），async 侧用 asyncio.to_thread 调用。
    """
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return "invalid-url", []
    if parts.scheme not in ("http", "https"):
        return "invalid-scheme", []
    if not parts.hostname:
        return "invalid-url", []
    default_port = 443 if parts.scheme == "https" else 80
    try:
        infos = socket.getaddrinfo(
            parts.hostname, parts.port or default_port, proto=socket.IPPROTO_TCP
        )
    except socket.gaierror:
        return "dns-failure", []
    except OSError:
        return "invalid-url", []
    ips = sorted({info[4][0] for info in infos})
    if not ips:
        return "dns-failure", []
    if any(_is_blocked_ip(ip) for ip in ips):
        return "intranet-or-reserved-ip", ips
    return "", ips


def _judge_embeddable(headers: httpx.Headers) -> tuple[bool, str]:
    """根据响应头判断页面能否被跨站 iframe 嵌入。"""
    xfo = (headers.get("x-frame-options") or "").strip().lower()
    if xfo in ("deny", "sameorigin"):
        return False, f"xfo-{xfo}"
    csp = headers.get("content-security-policy") or ""
    for directive in csp.split(";"):
        parts = directive.strip().split()
        if parts and parts[0].lower() == "frame-ancestors":
            values = [v.lower() for v in parts[1:]]
            if not values:
                break  # 空指令视为未声明
            if "*" in values or "http:" in values or "https:" in values:
                return True, "csp-wildcard"
            # 'none' / 'self' / 具体源列表：跨站工作台一律不可嵌
            return False, "csp-frame-ancestors"
    return True, "no-embed-restriction"


def _build_probe_client() -> httpx.AsyncClient:
    """探测客户端工厂（独立出来便于单测注入 MockTransport）。"""
    return httpx.AsyncClient(
        timeout=_PROBE_TIMEOUT,
        follow_redirects=False,
        headers={"User-Agent": _PROBE_USER_AGENT},
    )


async def _probe_url(url: str) -> dict:
    """跟随重定向逐跳校验并读取最终响应头，判定可嵌性。"""
    current = url
    try:
        async with _build_probe_client() as client:
            for _ in range(_MAX_REDIRECTS + 1):
                reason, _ips = await asyncio.to_thread(validate_public_http_url, current)
                if reason:
                    return {"embeddable": False, "reason": reason}
                try:
                    # stream 且不读 body：判定只需要响应头
                    async with client.stream("GET", current) as resp:
                        if resp.is_redirect:
                            location = resp.headers.get("location")
                            if not location:
                                return {
                                    "embeddable": True,
                                    "reason": f"status-{resp.status_code}",
                                }
                            current = urljoin(current, location)
                            continue
                        embeddable, why = _judge_embeddable(resp.headers)
                        return {"embeddable": embeddable, "reason": why}
                except httpx.TimeoutException:
                    return {"embeddable": False, "reason": "timeout"}
                except httpx.HTTPError:
                    return {"embeddable": False, "reason": "network-error"}
    except httpx.HTTPError:
        return {"embeddable": False, "reason": "network-error"}
    return {"embeddable": False, "reason": "too-many-redirects"}


def _cache_get(key: str) -> dict | None:
    hit = _EMBED_CHECK_CACHE.get(key)
    if hit is None:
        return None
    ts, value = hit
    if time.monotonic() - ts < _CACHE_TTL_SECONDS:
        return value
    _EMBED_CHECK_CACHE.pop(key, None)
    return None


def _cache_put(key: str, value: dict) -> None:
    if len(_EMBED_CHECK_CACHE) >= _CACHE_MAX_ENTRIES:
        oldest = min(_EMBED_CHECK_CACHE, key=lambda k: _EMBED_CHECK_CACHE[k][0])
        _EMBED_CHECK_CACHE.pop(oldest, None)
    _EMBED_CHECK_CACHE[key] = (time.monotonic(), value)


@url_probe.get("/url-embed-check")
async def url_embed_check(
    url: str = Query(..., min_length=8, max_length=2048),
    _current_user: object = Depends(get_required_user),
) -> dict:
    """检查目标 URL 能否被工作台 iframe 跨站嵌入。

    返回 {"embeddable": bool, "reason": str, "checkedUrl": str, "cached": bool}。
    探测自身异常时保守返回可嵌，前端回退到「尝试内嵌 + 超时兜底」的原有路径。
    """
    try:
        normalized = _normalize_url(url)
    except ValueError:
        return {"embeddable": False, "reason": "invalid-url", "checkedUrl": url, "cached": False}

    cached = _cache_get(normalized)
    if cached is not None:
        return {**cached, "checkedUrl": normalized, "cached": True}

    try:
        result = await _probe_url(normalized)
    except Exception:
        logger.exception("url-embed-check 探测异常: %s", normalized)
        result = {"embeddable": True, "reason": "probe-error"}
    _cache_put(normalized, result)
    return {**result, "checkedUrl": normalized, "cached": False}
