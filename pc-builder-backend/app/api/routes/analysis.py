from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession, OptionalUser
from app.core.config import settings
from app.core.security import constant_time_token_match
from app.models.entities import Build, BuildComponent, Offer, Product
from app.schemas.analysis import BuildAnalysisResponse
from app.schemas.builds import BuildRequirements
from app.services.bottleneck import bottleneck_service
from app.services.cache import cache
from app.services.compatibility import compatibility_engine
from app.services.performance import performance_service
from app.services.recommendations import recommendation_service

router = APIRouter(prefix="/builds", tags=["build-analysis"])

BUILD_ANALYSIS_LOAD = (
    selectinload(Build.components)
    .selectinload(BuildComponent.product)
    .selectinload(Product.offers)
    .selectinload(Offer.store),
    selectinload(Build.components)
    .selectinload(BuildComponent.product)
    .selectinload(Product.benchmarks),
    selectinload(Build.components)
    .selectinload(BuildComponent.selected_offer)
    .selectinload(Offer.store),
)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _can_read(build: Build, user, raw_token: str | None) -> bool:
    if build.visibility in {"public", "unlisted"}:
        return True
    if user and build.owner_id == user.id:
        return True
    return bool(
        raw_token
        and build.access_token_hash
        and constant_time_token_match(raw_token, build.access_token_hash)
    )


@router.get("/{build_id}/analysis", response_model=BuildAnalysisResponse)
async def analyze_build(
    build_id: UUID,
    session: DbSession,
    user: OptionalUser,
    build_token: str | None = Header(default=None, alias="X-Build-Token"),
    language: str | None = Query(default=None, pattern="^(uk|en|pl|ru)$"),
    refresh: bool = False,
) -> BuildAnalysisResponse:
    result = await session.execute(
        select(Build)
        .options(*BUILD_ANALYSIS_LOAD)
        .where(Build.id == build_id, Build.deleted_at.is_(None))
    )
    build = result.scalar_one_or_none()
    if build is None:
        raise HTTPException(status_code=404, detail="Build not found")
    expires = _aware(build.expires_at)
    if not build.is_saved and expires and expires <= datetime.now(UTC):
        raise HTTPException(status_code=410, detail="Temporary build expired")
    if not _can_read(build, user, build_token):
        raise HTTPException(status_code=403, detail="No access to this build")

    requirements = BuildRequirements.model_validate(build.requirements)
    if language:
        requirements.language = language
    cache_key = f"build-analysis:{build.id}:{build.version}:{requirements.language}"
    if not refresh:
        cached = await cache.get_json(cache_key)
        if cached:
            return BuildAnalysisResponse.model_validate(cached)

    components = {item.category: item.product for item in build.components}
    bottleneck = await bottleneck_service.assess_with_recommendations(
        session,
        components,
        requirements.resolution,
        requirements.language,
        build.currency,
        limit=3,
    )
    performance = await performance_service.estimate(
        session, components, requirements, limit=settings.analysis_max_workloads
    )
    upsell = await recommendation_service.upsell(
        session,
        components,
        requirements,
        build.currency,
        limit=settings.upsell_recommendation_limit,
    )
    peak_power = compatibility_engine.estimated_peak_power_w(components)
    cpu = components.get("cpu")
    gpu = components.get("gpu")
    recommended_psu = (
        compatibility_engine.required_psu_w(cpu, gpu) if cpu is not None and gpu is not None else 0
    )
    response = BuildAnalysisResponse(
        build_id=build.id,
        bottleneck=bottleneck,
        performance=performance,
        upsell=upsell,
        estimated_peak_power_w=peak_power,
        recommended_psu_w=recommended_psu,
    )
    await cache.set_json(
        cache_key, response.model_dump(mode="json"), settings.analysis_cache_ttl_seconds
    )
    return response
