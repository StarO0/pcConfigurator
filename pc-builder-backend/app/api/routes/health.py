from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Response, status
from sqlalchemy import func, select, text

from app.api.deps import DbSession
from app.core.config import settings
from app.models.entities import Offer, ParserRun
from app.services.cache import cache

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health(session: DbSession) -> dict:
    database = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        database = "error"
    return {
        "status": "ok" if database == "ok" else "degraded",
        "database": database,
        "cache": cache.backend_name,
        "environment": settings.environment,
        "version": settings.app_version,
    }


@router.get("/ready")
async def readiness(session: DbSession, response: Response) -> dict:
    try:
        await session.execute(text("SELECT 1"))
        product_offer_count = (
            await session.scalar(
                select(func.count(Offer.id)).where(
                    Offer.is_active.is_(True), Offer.in_stock.is_(True)
                )
            )
            or 0
        )
        recent_failure = (
            await session.scalar(
                select(func.count(ParserRun.id)).where(
                    ParserRun.status == "failed",
                    ParserRun.started_at >= datetime.now(UTC) - timedelta(hours=24),
                )
            )
            or 0
        )
        ready = product_offer_count > 0
        if not ready:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "ready": ready,
            "active_offers": product_offer_count,
            "parser_failures_24h": recent_failure,
        }
    except Exception as exc:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"ready": False, "error": type(exc).__name__}


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {"status": "alive"}
