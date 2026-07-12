from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Callable
from uuid import uuid4

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import request_id_ctx, user_id_ctx
from app.core.security import decode_access_token
from app.services.cache import cache

logger = logging.getLogger(__name__)

HTTP_REQUESTS = Counter(
    "pc_builder_http_requests_total",
    "Total HTTP requests",
    ("method", "route", "status"),
)
HTTP_LATENCY = Histogram(
    "pc_builder_http_request_duration_seconds",
    "HTTP request latency",
    ("method", "route"),
)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid4()))[:100]
        request_token = request_id_ctx.set(request_id)
        user_token = user_id_ctx.set(None)
        request.state.request_id = request_id
        started = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            elapsed = time.perf_counter() - started
            route = getattr(request.scope.get("route"), "path", request.url.path)
            status_code = response.status_code if response is not None else 500
            if settings.enable_metrics:
                HTTP_REQUESTS.labels(request.method, route, str(status_code)).inc()
                HTTP_LATENCY.labels(request.method, route).observe(elapsed)
            logger.info(
                "request_complete method=%s path=%s status=%s latency_ms=%s",
                request.method,
                request.url.path,
                status_code,
                int(elapsed * 1000),
            )
            if response is not None:
                response.headers["X-Request-ID"] = request_id
            user_id_ctx.reset(user_token)
            request_id_ctx.reset(request_token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
        if settings.environment == "production":
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response


class BodyLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > settings.max_request_body_bytes:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"detail": "Request body is too large"},
                    )
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length"})
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    excluded_prefixes = ("/docs", "/redoc", "/openapi.json", "/metrics", "/api/v1/health")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if settings.environment == "test" or request.url.path.startswith(self.excluded_prefixes):
            return await call_next(request)
        authorization = request.headers.get("authorization", "")
        claims = (
            decode_access_token(authorization.removeprefix("Bearer ").strip())
            if authorization.startswith("Bearer ")
            else None
        )
        identity = (
            f"user:{claims.user_id}"
            if claims
            else f"ip:{request.client.host if request.client else 'unknown'}"
        )
        limit = (
            settings.rate_limit_authenticated_per_minute
            if claims
            else settings.rate_limit_anonymous_per_minute
        )
        bucket = int(time.time() // 60)
        count = await cache.increment_window(f"rate:{identity}:{bucket}", 70)
        if count > limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Слишком много запросов. Повторите позже."},
                headers={"Retry-After": "60"},
            )
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        return response


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        key = request.headers.get(settings.idempotency_header)
        if not key or request.method not in {"POST", "PUT", "PATCH"}:
            return await call_next(request)
        if len(key) > 200:
            return JSONResponse(status_code=400, content={"detail": "Invalid idempotency key"})
        auth = request.headers.get("authorization", "anonymous")
        digest = hashlib.sha256(
            f"{request.method}:{request.url.path}:{auth}:{key}".encode()
        ).hexdigest()
        cache_key = f"idempotency:{digest}"
        cached = await cache.get_json(cache_key)
        if cached:
            return JSONResponse(
                status_code=cached["status"],
                content=cached["body"],
                headers={"X-Idempotent-Replay": "true"},
            )
        if not await cache.acquire_lock(f"{cache_key}:lock", 30):
            return JSONResponse(
                status_code=409,
                content={"detail": "Request with this idempotency key is already processing"},
            )
        response = await call_next(request)
        body = b"".join([chunk async for chunk in response.body_iterator])
        try:
            parsed = json.loads(body) if body else None
        except json.JSONDecodeError:
            parsed = None
        if response.status_code < 500 and parsed is not None:
            await cache.set_json(
                cache_key,
                {"status": response.status_code, "body": parsed},
                86400,
            )
        headers = dict(response.headers)
        headers.pop("content-length", None)
        return Response(
            content=body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
            background=response.background,
        )
