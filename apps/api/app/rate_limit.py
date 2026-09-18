from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from redis import asyncio as redis_asyncio
from redis.exceptions import RedisError
from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


class AnonymousChatRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()
        self.redis = redis_asyncio.from_url(get_settings().redis_url, socket_connect_timeout=0.1, socket_timeout=0.1)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method != "POST" or request.url.path != "/api/v1/chat/stream":
            return await call_next(request)
        client_ip = request.client.host if request.client else "unknown"
        limit = get_settings().anonymous_chat_requests_per_minute
        try:
            key = f"deep-geology:anonymous-chat:{client_ip}"
            request_count = await self.redis.incr(key)
            if request_count == 1:
                await self.redis.expire(key, 60)
            if request_count > limit:
                return JSONResponse(status_code=429, content={"detail": "Anonymous chat rate limit exceeded"})
            return await call_next(request)
        except RedisError:
            return await self._fallback_limit(client_ip, limit, call_next, request)

    async def _fallback_limit(self, client_ip: str, limit: int, call_next, request: Request) -> Response:
        now = monotonic()
        with self.lock:
            timestamps = self.requests[client_ip]
            while timestamps and now - timestamps[0] >= 60:
                timestamps.popleft()
            if len(timestamps) >= limit:
                return JSONResponse(status_code=429, content={"detail": "Anonymous chat rate limit exceeded"})
            timestamps.append(now)
        return await call_next(request)
