from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.exc import IntegrityError
from starlette.responses import Response

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import (
    BodyLimitMiddleware,
    IdempotencyMiddleware,
    RateLimitMiddleware,
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
)
from app.db.base import Base
from app.db.seed import seed_demo_data
from app.db.session import AsyncSessionLocal, engine
from app.db.starter_snapshot import ensure_bootstrap_admin, seed_starter_snapshot
from app.services.cache import cache
from app.services.harvester.scheduler import scheduler_loop
from app.services.parsers.source_seed import seed_source_stores

configure_logging()
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1,
        send_default_pii=False,
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    if settings.seed_demo_data:
        async with AsyncSessionLocal() as session:
            await seed_demo_data(session)
    elif settings.starter_snapshot_enabled:
        async with AsyncSessionLocal() as session:
            await seed_starter_snapshot(session)
    async with AsyncSessionLocal() as session:
        await ensure_bootstrap_admin(session)
        await session.commit()
    async with AsyncSessionLocal() as session:
        await seed_source_stores(session)
    await cache.connect()
    scheduler_task = (
        asyncio.create_task(scheduler_loop(), name="catalog-harvester-scheduler")
        if settings.harvester_scheduler_enabled
        else None
    )
    yield
    if scheduler_task:
        scheduler_task.cancel()
        with suppress(asyncio.CancelledError):
            await scheduler_task
    await cache.close()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Production-oriented AI-assisted PC configurator. AI parses user intent and explains "
        "results; deterministic code validates compatibility and selects products."
    ),
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_host_list)
if settings.force_https:
    app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Build-Token",
        "X-Service-Token",
        "Idempotency-Key",
        "X-Request-ID",
    ],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(BodyLimitMiddleware)
app.add_middleware(RequestContextMiddleware)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        sanitized = dict(error)
        sanitized.pop("ctx", None)
        errors.append(sanitized)
    return JSONResponse(
        status_code=422,
        content={"detail": "Ошибка валидации", "errors": jsonable_encoder(errors)},
    )


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(_: Request, __: IntegrityError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": "Конфликт данных"})


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs" if settings.environment != "production" else "disabled",
        "health": f"{settings.api_v1_prefix}/health",
    }


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    if not settings.enable_metrics:
        return Response(status_code=404)
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
