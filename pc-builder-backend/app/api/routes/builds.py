from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, Request, status
from fastapi.responses import ORJSONResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import StaleDataError

from app.api.deps import CurrentUser, DbSession, OptionalUser
from app.core.security import constant_time_token_match
from app.models.entities import Build, BuildComponent, BuildRevision, Offer, Product
from app.schemas.builds import (
    BuildCompareRequest,
    BuildCompareResponse,
    BuildOut,
    BuildRevisionOut,
    BuildUpdateRequest,
    CloneBuildRequest,
    ComponentDifference,
    GenerateBuildRequest,
    GenerateBuildResponse,
    GeneratedBuildOut,
    ReplaceComponentRequest,
    ReplacementOption,
    RepriceBuildRequest,
)
from app.schemas.common import MessageResponse
from app.services.ai.service import ai_service
from app.services.audit import audit
from app.services.build_generator import build_generator
from app.services.builds import create_build_revision
from app.services.cache import cache
from app.services.compatibility import compatibility_engine
from app.services.pricing import optimize_basket
from app.services.serializers import build_to_schema, product_to_schema

router = APIRouter(prefix="/builds", tags=["builds"])

BUILD_LOAD = (
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


def aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def load_build(session: DbSession, build_id: UUID, include_deleted: bool = False) -> Build:
    filters = [Build.id == build_id]
    if not include_deleted:
        filters.append(Build.deleted_at.is_(None))
    result = await session.execute(select(Build).options(*BUILD_LOAD).where(*filters))
    build = result.scalar_one_or_none()
    if build is None:
        raise HTTPException(status_code=404, detail="Сборка не найдена")
    return build


def can_read(build: Build, user, raw_token: str | None) -> bool:
    if build.visibility in {"public", "unlisted"}:
        return True
    if user and build.owner_id == user.id:
        return True
    return bool(
        raw_token
        and build.access_token_hash
        and constant_time_token_match(raw_token, build.access_token_hash)
    )


def can_edit(build: Build, user, raw_token: str | None) -> bool:
    if user and build.owner_id == user.id:
        return True
    return bool(
        raw_token
        and build.access_token_hash
        and constant_time_token_match(raw_token, build.access_token_hash)
    )


def ensure_not_expired(build: Build) -> None:
    expires = aware(build.expires_at)
    if not build.is_saved and expires and expires <= datetime.now(UTC):
        raise HTTPException(status_code=410, detail="Временная сборка истекла")


@router.post("/generate", response_model=GenerateBuildResponse)
async def generate_builds(
    payload: GenerateBuildRequest,
    session: DbSession,
    user: OptionalUser,
) -> GenerateBuildResponse:
    user_id = user.id if user else None
    normalized_prompt = " ".join(payload.prompt.strip().lower().split())
    prompt_key = f"prompt-parse:{hashlib.sha256(normalized_prompt.encode()).hexdigest()}"
    cached_requirements = await cache.get_json(prompt_key)
    if cached_requirements:
        from app.schemas.builds import BuildRequirements

        requirements = BuildRequirements.model_validate(cached_requirements)
    else:
        requirements = await ai_service.parse_requirements(
            payload.prompt,
            session=session,
            user_id=user_id,
        )
        await cache.set_json(prompt_key, requirements.model_dump(mode="json"), 86400)
    if payload.budget is not None:
        requirements.budget = payload.budget
    if payload.currency is not None:
        requirements.currency = payload.currency.upper()

    requirements_from_cache = bool(cached_requirements)

    try:
        generated = await build_generator.generate(
            session=session,
            prompt=payload.prompt,
            requirements=requirements,
            basket_mode=payload.basket_mode,
            owner_id=None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    response_builds: list[GeneratedBuildOut] = []
    for item in generated:
        build = await load_build(session, item.build.id)
        response_builds.append(
            GeneratedBuildOut(
                **build_to_schema(build).model_dump(),
                access_token=item.access_token,
            )
        )
    await session.commit()  # AI usage rows can still be pending after generator commit.
    return GenerateBuildResponse(
        requirements=requirements,
        builds=response_builds,
        cached=requirements_from_cache,
    )


@router.get("/saved/me/list", response_model=list[BuildOut])
async def saved_builds(session: DbSession, user: CurrentUser) -> list[BuildOut]:
    result = await session.execute(
        select(Build)
        .options(*BUILD_LOAD)
        .where(Build.owner_id == user.id, Build.is_saved.is_(True), Build.deleted_at.is_(None))
        .order_by(Build.updated_at.desc())
    )
    return [build_to_schema(build) for build in result.scalars().unique()]


@router.get("/trash/me/list", response_model=list[BuildOut])
async def trashed_builds(session: DbSession, user: CurrentUser) -> list[BuildOut]:
    result = await session.execute(
        select(Build)
        .options(*BUILD_LOAD)
        .where(Build.owner_id == user.id, Build.deleted_at.is_not(None))
        .order_by(Build.deleted_at.desc())
    )
    return [build_to_schema(build) for build in result.scalars().unique()]


@router.get("/public/{public_slug}", response_model=BuildOut)
async def public_build(public_slug: str, session: DbSession) -> BuildOut:
    result = await session.execute(
        select(Build)
        .options(*BUILD_LOAD)
        .where(
            Build.public_slug == public_slug,
            Build.visibility.in_(["public", "unlisted"]),
            Build.deleted_at.is_(None),
        )
    )
    build = result.scalar_one_or_none()
    if build is None:
        raise HTTPException(status_code=404, detail="Публичная сборка не найдена")
    return build_to_schema(build)


@router.post("/compare", response_model=BuildCompareResponse)
async def compare_builds(
    payload: BuildCompareRequest,
    session: DbSession,
    user: OptionalUser,
) -> BuildCompareResponse:
    left = await load_build(session, payload.left_id)
    right = await load_build(session, payload.right_id)
    ensure_not_expired(left)
    ensure_not_expired(right)
    if not can_read(left, user, payload.left_token) or not can_read(
        right, user, payload.right_token
    ):
        raise HTTPException(status_code=403, detail="Нет доступа к одной из сборок")

    left_schema = build_to_schema(left)
    right_schema = build_to_schema(right)
    left_components = {item.category: item for item in left_schema.components}
    right_components = {item.category: item for item in right_schema.components}
    differences: list[ComponentDifference] = []
    for category in sorted(set(left_components) | set(right_components)):
        left_item = left_components.get(category)
        right_item = right_components.get(category)
        differences.append(
            ComponentDifference(
                category=category,
                left_product_id=left_item.product.id if left_item else None,
                left_name=left_item.product.name if left_item else None,
                left_price=(
                    left_item.selected_offer.effective_price
                    if left_item and left_item.selected_offer
                    else None
                ),
                right_product_id=right_item.product.id if right_item else None,
                right_name=right_item.product.name if right_item else None,
                right_price=(
                    right_item.selected_offer.effective_price
                    if right_item and right_item.selected_offer
                    else None
                ),
                same_product=bool(
                    left_item and right_item and left_item.product.id == right_item.product.id
                ),
            )
        )
    return BuildCompareResponse(
        left=left_schema,
        right=right_schema,
        total_price_delta=right.total_price - left.total_price,
        delivery_price_delta=right.delivery_price - left.delivery_price,
        store_count_delta=right.store_count - left.store_count,
        differences=differences,
    )


@router.get("/{build_id}", response_model=BuildOut)
async def get_build(
    build_id: UUID,
    session: DbSession,
    user: OptionalUser,
    build_token: str | None = Header(default=None, alias="X-Build-Token"),
) -> BuildOut:
    build = await load_build(session, build_id)
    ensure_not_expired(build)
    if not can_read(build, user, build_token):
        raise HTTPException(status_code=403, detail="Нет доступа к сборке")
    return build_to_schema(build)


@router.get("/{build_id}/replacement-options/{category}", response_model=list[ReplacementOption])
async def replacement_options(
    build_id: UUID,
    category: str,
    session: DbSession,
    user: OptionalUser,
    build_token: str | None = Header(default=None, alias="X-Build-Token"),
    compatible_only: bool = True,
    max_price: Decimal | None = Query(default=None, ge=0),
    brand: list[str] = Query(default=[]),
    sort: str = Query(default="price", pattern="^(price|performance|noise|upgrade)$"),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[ReplacementOption]:
    build = await load_build(session, build_id)
    ensure_not_expired(build)
    if not can_read(build, user, build_token):
        raise HTTPException(status_code=403, detail="Нет доступа к сборке")
    current = {component.category: component.product for component in build.components}
    if category not in current:
        raise HTTPException(status_code=400, detail="Такой категории нет в сборке")

    filters = [
        Product.category == category,
        Product.is_active.is_(True),
        Product.status == "active",
    ]
    if brand:
        filters.append(Product.brand.in_(brand))
    result = await session.execute(
        select(Product)
        .options(
            selectinload(Product.offers).selectinload(Offer.store),
            selectinload(Product.benchmarks),
        )
        .where(*filters)
    )
    options: list[ReplacementOption] = []
    for product in result.scalars().unique():
        candidate_map = dict(current)
        candidate_map[category] = product
        issues = compatibility_engine.validate(candidate_map)
        is_compatible = not any(issue.severity == "error" for issue in issues)
        if compatible_only and not is_compatible:
            continue
        basket = optimize_basket(
            candidate_map,
            build.currency,
            mode="balanced",
            max_store_count=build.requirements.get("max_store_count"),
        )
        if basket is None or (max_price is not None and basket.total_price > max_price):
            continue
        options.append(
            ReplacementOption(
                product=product_to_schema(product),
                is_compatible=is_compatible,
                issues=issues,
                projected_total=basket.total_price,
            )
        )
    if sort == "performance":
        options.sort(key=lambda option: (-option.product.performance_score, option.projected_total))
    elif sort == "noise":
        options.sort(key=lambda option: (-option.product.noise_score, option.projected_total))
    elif sort == "upgrade":
        options.sort(key=lambda option: (-option.product.upgrade_score, option.projected_total))
    else:
        options.sort(key=lambda option: (not option.is_compatible, option.projected_total))
    return options[:limit]


@router.patch("/{build_id}/components/{category}", response_model=BuildOut)
async def replace_component(
    build_id: UUID,
    category: str,
    payload: ReplaceComponentRequest,
    session: DbSession,
    request: Request,
    user: OptionalUser,
    build_token: str | None = Header(default=None, alias="X-Build-Token"),
) -> BuildOut:
    build = await load_build(session, build_id)
    ensure_not_expired(build)
    if not can_edit(build, user, build_token):
        raise HTTPException(status_code=403, detail="Нет прав на изменение сборки")
    if build.version != payload.expected_version:
        raise HTTPException(
            status_code=409,
            detail={"message": "Сборка уже изменена", "current_version": build.version},
        )
    component = next((item for item in build.components if item.category == category), None)
    if component is None:
        raise HTTPException(status_code=400, detail="Такой категории нет в сборке")
    result = await session.execute(
        select(Product)
        .options(
            selectinload(Product.offers).selectinload(Offer.store), selectinload(Product.benchmarks)
        )
        .where(
            Product.id == payload.product_id,
            Product.category == category,
            Product.is_active.is_(True),
            Product.status == "active",
        )
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Подходящий товар не найден")

    candidate_map = {item.category: item.product for item in build.components}
    candidate_map[category] = product
    issues = compatibility_engine.validate(candidate_map)
    if any(issue.severity == "error" for issue in issues):
        explanation = await ai_service.explain_compatibility(
            issues,
            session=session,
            user_id=user.id if user else None,
        )
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Компонент несовместим со сборкой",
                "explanation": explanation,
                "issues": [item.model_dump() for item in issues],
            },
        )
    basket = optimize_basket(
        candidate_map,
        build.currency,
        mode=payload.basket_mode,
        max_store_count=build.requirements.get("max_store_count"),
    )
    if basket is None:
        raise HTTPException(status_code=409, detail="Нет доступной корзины для этого набора")

    await create_build_revision(session, build, "replace_component")
    component.product_id = product.id
    component.product = product
    for item in build.components:
        item.selected_offer_id = basket.offers[item.category].id
        item.selected_offer = basket.offers[item.category]
    build.total_price = basket.total_price
    build.delivery_price = basket.delivery_price
    build.store_count = basket.store_count
    summary = [
        {
            "category": key,
            "name": value.name,
            "specs": value.specs,
            "price": float(basket.offers[key].price),
        }
        for key, value in candidate_map.items()
    ]
    build.explanation = await ai_service.explain_build(
        build_to_schema(build).requirements,
        build.profile,
        summary,
        float(build.total_price),
        session=session,
        user_id=user.id if user else None,
    )
    await audit(
        session,
        request,
        "build.component_replace",
        "build",
        build.id,
        user_id=user.id if user else None,
        details={"category": category, "product_id": str(product.id)},
    )
    try:
        await session.commit()
    except StaleDataError as exc:
        raise HTTPException(status_code=409, detail="Сборка была изменена параллельно") from exc
    return build_to_schema(await load_build(session, build.id))


@router.patch("/{build_id}", response_model=BuildOut)
async def update_build(
    build_id: UUID,
    payload: BuildUpdateRequest,
    session: DbSession,
    request: Request,
    user: OptionalUser,
    build_token: str | None = Header(default=None, alias="X-Build-Token"),
) -> BuildOut:
    build = await load_build(session, build_id)
    if not can_edit(build, user, build_token):
        raise HTTPException(status_code=403, detail="Нет прав на изменение сборки")
    if build.version != payload.expected_version:
        raise HTTPException(
            status_code=409,
            detail={"message": "Сборка уже изменена", "current_version": build.version},
        )
    if payload.visibility and not user:
        raise HTTPException(status_code=401, detail="Публиковать сборки можно только после входа")
    await create_build_revision(session, build, "metadata_update")
    if payload.name is not None:
        build.name = payload.name.strip()
    if payload.visibility is not None:
        build.visibility = payload.visibility
        if payload.visibility in {"public", "unlisted"} and not build.public_slug:
            build.public_slug = secrets.token_urlsafe(9)
        if payload.visibility == "private":
            build.public_slug = None
    await audit(
        session, request, "build.update", "build", build.id, user_id=user.id if user else None
    )
    await session.commit()
    return build_to_schema(await load_build(session, build.id))


@router.post("/{build_id}/reprice", response_model=BuildOut)
async def reprice_build(
    build_id: UUID,
    payload: RepriceBuildRequest,
    session: DbSession,
    request: Request,
    user: OptionalUser,
    build_token: str | None = Header(default=None, alias="X-Build-Token"),
) -> BuildOut:
    build = await load_build(session, build_id)
    if not can_edit(build, user, build_token):
        raise HTTPException(status_code=403, detail="Нет прав на изменение сборки")
    if build.version != payload.expected_version:
        raise HTTPException(
            status_code=409,
            detail={"message": "Сборка уже изменена", "current_version": build.version},
        )
    products = {item.category: item.product for item in build.components}
    basket = optimize_basket(
        products,
        build.currency,
        mode=payload.basket_mode,
        max_store_count=build.requirements.get("max_store_count"),
    )
    if basket is None:
        raise HTTPException(status_code=409, detail="Некоторые детали больше не продаются")
    await create_build_revision(session, build, "reprice")
    for item in build.components:
        item.selected_offer_id = basket.offers[item.category].id
        item.selected_offer = basket.offers[item.category]
    build.total_price = basket.total_price
    build.delivery_price = basket.delivery_price
    build.store_count = basket.store_count
    await audit(
        session, request, "build.reprice", "build", build.id, user_id=user.id if user else None
    )
    await session.commit()
    return build_to_schema(await load_build(session, build.id))


@router.post("/{build_id}/save", response_model=BuildOut)
async def save_build(
    build_id: UUID,
    session: DbSession,
    request: Request,
    user: CurrentUser,
    build_token: str | None = Header(default=None, alias="X-Build-Token"),
) -> BuildOut:
    build = await load_build(session, build_id)
    if build.owner_id not in (None, user.id):
        raise HTTPException(status_code=403, detail="Эта сборка принадлежит другому пользователю")
    if build.owner_id is None and not can_edit(build, user, build_token):
        raise HTTPException(status_code=403, detail="Нужен токен временной сборки")
    build.owner_id = user.id
    build.is_saved = True
    build.expires_at = None
    build.access_token_hash = None
    await audit(session, request, "build.save", "build", build.id, user_id=user.id)
    await session.commit()
    return build_to_schema(await load_build(session, build.id))


@router.post("/{build_id}/clone", response_model=BuildOut, status_code=status.HTTP_201_CREATED)
async def clone_build(
    build_id: UUID,
    payload: CloneBuildRequest,
    session: DbSession,
    user: CurrentUser,
) -> BuildOut:
    source = await load_build(session, build_id)
    if not can_read(source, user, None):
        raise HTTPException(status_code=403, detail="Нет доступа к сборке")
    clone = Build(
        owner_id=user.id,
        name=payload.name or f"Копия: {source.name}",
        prompt=source.prompt,
        profile=source.profile,
        title=source.title,
        requirements=source.requirements,
        explanation=source.explanation,
        budget=source.budget,
        currency=source.currency,
        total_price=source.total_price,
        delivery_price=source.delivery_price,
        store_count=source.store_count,
        is_saved=True,
    )
    session.add(clone)
    await session.flush()
    for item in source.components:
        session.add(
            BuildComponent(
                build_id=clone.id,
                category=item.category,
                product_id=item.product_id,
                selected_offer_id=item.selected_offer_id,
                quantity=item.quantity,
            )
        )
    await session.commit()
    return build_to_schema(await load_build(session, clone.id))


@router.get("/{build_id}/revisions", response_model=list[BuildRevisionOut])
async def build_revisions(
    build_id: UUID, session: DbSession, user: CurrentUser
) -> list[BuildRevisionOut]:
    build = await load_build(session, build_id)
    if build.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    result = await session.execute(
        select(BuildRevision)
        .where(BuildRevision.build_id == build_id)
        .order_by(BuildRevision.revision.desc())
    )
    return [
        BuildRevisionOut(
            revision=item.revision,
            reason=item.reason,
            snapshot=item.snapshot,
            created_at=item.created_at,
        )
        for item in result.scalars()
    ]


@router.delete("/{build_id}", response_model=MessageResponse)
async def delete_build(
    build_id: UUID, session: DbSession, request: Request, user: CurrentUser
) -> MessageResponse:
    build = await load_build(session, build_id)
    if build.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    build.deleted_at = datetime.now(UTC)
    await audit(session, request, "build.delete", "build", build.id, user_id=user.id)
    await session.commit()
    return MessageResponse(message="Сборка перемещена в корзину")


@router.post("/{build_id}/restore", response_model=BuildOut)
async def restore_build(build_id: UUID, session: DbSession, user: CurrentUser) -> BuildOut:
    build = await load_build(session, build_id, include_deleted=True)
    if build.owner_id != user.id or build.deleted_at is None:
        raise HTTPException(status_code=404, detail="Удалённая сборка не найдена")
    build.deleted_at = None
    await session.commit()
    return build_to_schema(await load_build(session, build.id))


@router.get("/{build_id}/export", response_class=ORJSONResponse)
async def export_build(
    build_id: UUID,
    session: DbSession,
    user: OptionalUser,
    build_token: str | None = Header(default=None, alias="X-Build-Token"),
) -> ORJSONResponse:
    build = await load_build(session, build_id)
    ensure_not_expired(build)
    if not can_read(build, user, build_token):
        raise HTTPException(status_code=403, detail="Нет доступа к сборке")
    payload = build_to_schema(build).model_dump(mode="json")
    return ORJSONResponse(
        content=payload,
        headers={
            "Content-Disposition": f'attachment; filename="pc-build-{build.id}.json"',
            "Cache-Control": "private, no-store",
        },
    )
