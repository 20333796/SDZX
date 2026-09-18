from time import perf_counter

from fastapi import Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

HTTP_REQUESTS = Counter(
    "deep_geology_http_requests_total",
    "HTTP requests handled by the platform API",
    ["method", "path", "status"],
)
HTTP_DURATION = Histogram(
    "deep_geology_http_request_duration_seconds",
    "HTTP request duration for the platform API",
    ["method", "path"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)
        started = perf_counter()
        response = await call_next(request)
        labels = {"method": request.method, "path": request.url.path}
        HTTP_REQUESTS.labels(status=str(response.status_code), **labels).inc()
        HTTP_DURATION.labels(**labels).observe(perf_counter() - started)
        return response


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
