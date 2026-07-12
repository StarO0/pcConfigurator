from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import StaleDataError

from app.api.deps import AdminUser, DbSession, OptionalUser, ServiceAuth
from app.core.config import settings
from app.core.security import generate_opaque_token, token_hash
from app.models.entities import (
    AuditLog,
    Build,
    BuildComponent,
    Offer,
    ParserRun,
    Product,
    ServiceToken,
    Store,
    User,
)
from app.schemas.admin import (
    AdminStatsOut,
    AdminUserUpdate,
    AuditLogOut,
    MergeProductsRequest,
    ParserRunOut,
    ServiceTokenCreate,
    ServiceTokenCreated,
    TaskQueuedResponse,
)
from app.schemas.auth import UserOut
from app.schemas.common import MessageResponse, Page
from app.schemas.products import (
    OfferImportRequest,
    OfferImportResponse,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    StoreCreate,
    StoreOut,
    StoreUpdate,
)
from app.services.audit import audit
from app.services.matching import normalize_text
from app.services.offer_import import import_offers
from app.services.serializers import product_to_schema, store_to_schema

router = APIRouter(prefix="/admin", tags=["admin"])


def require_import_auth(user, service_token) -> None:
    if user and user.role == "admin":
        return
    if service_token and "offers:write" in service_token.scopes:
        return
    raise HTTPException(
        status_code=403, detail="Требуются права admin или service token offers:write"
    )


@router.get("/stats", response_model=AdminStatsOut)
async def admin_stats(session: DbSession, _: AdminUser) -> AdminStatsOut:
    stale_before = datetime.now(UTC) - timedelta(hours=settings.offer_stale_hours)
    failed_since = datetime.now(UTC) - timedelta(hours=24)
    return AdminStatsOut(
        users=await session.scalar(select(func.count(User.id))) or 0,
        products=await session.scalar(
            select(func.count(Product.id)).where(Product.is_active.is_(True))
        )
        or 0,
        active_offers=await session.scalar(
            select(func.count(Offer.id)).where(Offer.is_active.is_(True), Offer.in_stock.is_(True))
        )
        or 0,
        saved_builds=await session.scalar(
            select(func.count(Build.id)).where(Build.is_saved.is_(True), Build.deleted_at.is_(None))
        )
        or 0,
        stale_offers=await session.scalar(
            select(func.count(Offer.id)).where(
                Offer.fetched_at < stale_before, Offer.is_active.is_(True)
            )
        )
        or 0,
        failed_parser_runs_24h=await session.scalar(
            select(func.count(ParserRun.id)).where(
                ParserRun.status == "failed", ParserRun.started_at >= failed_since
            )
        )
        or 0,
    )


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate, session: DbSession, request: Request, admin: AdminUser
) -> ProductOut:
    product = Product(
        category=payload.category.lower(),
        brand=payload.brand.strip(),
        name=payload.name.strip(),
        normalized_name=normalize_text(f"{payload.brand} {payload.name} {payload.sku}"),
        sku=payload.sku.strip(),
        ean=payload.ean,
        mpn=payload.mpn,
        image_url=str(payload.image_url) if payload.image_url else None,
        release_date=payload.release_date,
        performance_score=payload.performance_score,
        noise_score=payload.noise_score,
        upgrade_score=payload.upgrade_score,
        quality_score=payload.quality_score,
        specs=payload.specs,
        status=payload.status,
        is_active=payload.status == "active",
    )
    session.add(product)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="SKU/EAN уже существует") from exc
    await audit(session, request, "admin.product_create", "product", product.id, user_id=admin.id)
    await session.commit()
    result = await session.execute(
        select(Product)
        .options(
            selectinload(Product.offers).selectinload(Offer.store),
            selectinload(Product.benchmarks),
        )
        .where(Product.id == product.id)
    )
    return product_to_schema(result.scalar_one())


@router.patch("/products/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: UUID, payload: ProductUpdate, session: DbSession, request: Request, admin: AdminUser
) -> ProductOut:
    result = await session.execute(
        select(Product)
        .options(
            selectinload(Product.offers).selectinload(Offer.store), selectinload(Product.benchmarks)
        )
        .where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    if product.version != payload.version:
        raise HTTPException(
            status_code=409,
            detail={"message": "Товар уже изменён", "current_version": product.version},
        )
    values = payload.model_dump(exclude_unset=True, exclude={"version"})
    if "image_url" in values and values["image_url"] is not None:
        values["image_url"] = str(values["image_url"])
    for key, value in values.items():
        setattr(product, key, value)
    if "name" in values or "brand" in values:
        product.normalized_name = normalize_text(f"{product.brand} {product.name} {product.sku}")
    if product.status != "active":
        product.is_active = False
    await audit(
        session,
        request,
        "admin.product_update",
        "product",
        product.id,
        user_id=admin.id,
        details={"fields": list(values)},
    )
    try:
        await session.commit()
    except StaleDataError as exc:
        raise HTTPException(status_code=409, detail="Товар изменён параллельно") from exc
    return product_to_schema(product)


@router.delete("/products/{product_id}", response_model=MessageResponse)
async def deactivate_product(
    product_id: UUID, session: DbSession, request: Request, admin: AdminUser
) -> MessageResponse:
    product = await session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    product.is_active = False
    product.status = "discontinued"
    await audit(
        session, request, "admin.product_deactivate", "product", product.id, user_id=admin.id
    )
    await session.commit()
    return MessageResponse(message="Товар отключён")


@router.post("/products/merge", response_model=MessageResponse)
async def merge_products(
    payload: MergeProductsRequest, session: DbSession, request: Request, admin: AdminUser
) -> MessageResponse:
    if payload.source_product_id == payload.target_product_id:
        raise HTTPException(status_code=400, detail="Нужны разные товары")
    source = await session.get(Product, payload.source_product_id)
    target = await session.get(Product, payload.target_product_id)
    if source is None or target is None:
        raise HTTPException(status_code=404, detail="Один из товаров не найден")
    await session.execute(
        update(Offer).where(Offer.product_id == source.id).values(product_id=target.id)
    )
    await session.execute(
        update(BuildComponent)
        .where(BuildComponent.product_id == source.id)
        .values(product_id=target.id)
    )
    source.is_active = False
    source.status = "merged"
    await audit(
        session,
        request,
        "admin.product_merge",
        "product",
        target.id,
        user_id=admin.id,
        details={"source": str(source.id)},
    )
    await session.commit()
    return MessageResponse(message="Товары объединены")


@router.get("/stores", response_model=list[StoreOut])
async def list_stores(session: DbSession, _: AdminUser) -> list[StoreOut]:
    result = await session.execute(select(Store).order_by(Store.name))
    return [store_to_schema(item) for item in result.scalars()]


@router.post("/stores", response_model=StoreOut, status_code=status.HTTP_201_CREATED)
async def create_store(
    payload: StoreCreate, session: DbSession, request: Request, admin: AdminUser
) -> StoreOut:
    store = Store(
        slug=payload.slug,
        name=payload.name,
        base_url=str(payload.base_url),
        country=payload.country.upper(),
        parser_type=payload.parser_type,
        parser_config=payload.parser_config,
    )
    session.add(store)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409, detail="Магазин с таким slug/name уже существует"
        ) from exc
    await audit(session, request, "admin.store_create", "store", store.id, user_id=admin.id)
    await session.commit()
    return store_to_schema(store)


@router.patch("/stores/{store_id}", response_model=StoreOut)
async def update_store(
    store_id: UUID, payload: StoreUpdate, session: DbSession, request: Request, admin: AdminUser
) -> StoreOut:
    store = await session.get(Store, store_id)
    if store is None:
        raise HTTPException(status_code=404, detail="Магазин не найден")
    values = payload.model_dump(exclude_unset=True)
    if "base_url" in values and values["base_url"] is not None:
        values["base_url"] = str(values["base_url"])
    for key, value in values.items():
        setattr(store, key, value)
    await audit(session, request, "admin.store_update", "store", store.id, user_id=admin.id)
    await session.commit()
    return store_to_schema(store)


@router.post("/offers/import", response_model=OfferImportResponse)
async def import_offer_feed(
    payload: OfferImportRequest,
    session: DbSession,
    request: Request,
    user: OptionalUser,
    service_token: ServiceAuth,
) -> OfferImportResponse:
    require_import_auth(user, service_token)
    imported = await import_offers(
        session,
        payload.offers,
        create_unmatched_products=payload.create_unmatched_products,
    )
    await audit(
        session,
        request,
        "offers.import",
        "offer",
        user_id=user.id if user else None,
        service_token_id=service_token.id if service_token else None,
        details={
            "created": imported.created,
            "updated": imported.updated,
            "skipped": imported.skipped,
        },
    )
    await session.commit()
    return OfferImportResponse(
        created=imported.created,
        updated=imported.updated,
        skipped=imported.skipped,
        unmatched=imported.unmatched,
    )


@router.post(
    "/service-tokens", response_model=ServiceTokenCreated, status_code=status.HTTP_201_CREATED
)
async def create_service_token(
    payload: ServiceTokenCreate, session: DbSession, request: Request, admin: AdminUser
) -> ServiceTokenCreated:
    raw = generate_opaque_token()
    item = ServiceToken(
        name=payload.name,
        token_hash=token_hash(raw),
        scopes=payload.scopes,
        expires_at=payload.expires_at,
    )
    session.add(item)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409, detail="Service token с таким именем уже существует"
        ) from exc
    await audit(
        session,
        request,
        "admin.service_token_create",
        "service_token",
        item.id,
        user_id=admin.id,
        details={"scopes": item.scopes},
    )
    await session.commit()
    return ServiceTokenCreated(
        id=item.id, name=item.name, token=raw, scopes=item.scopes, expires_at=item.expires_at
    )


@router.delete("/service-tokens/{token_id}", response_model=MessageResponse)
async def revoke_service_token(
    token_id: UUID, session: DbSession, request: Request, admin: AdminUser
) -> MessageResponse:
    item = await session.get(ServiceToken, token_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Service token не найден")
    item.is_active = False
    await audit(
        session, request, "admin.service_token_revoke", "service_token", item.id, user_id=admin.id
    )
    await session.commit()
    return MessageResponse(message="Service token отозван")


@router.post(
    "/stores/{store_id}/sync",
    response_model=TaskQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def queue_store_sync(store_id: UUID, session: DbSession, _: AdminUser) -> TaskQueuedResponse:
    store = await session.get(Store, store_id)
    if store is None or not store.is_active:
        raise HTTPException(status_code=404, detail="Активный магазин не найден")
    if store.parser_type == "manual":
        raise HTTPException(status_code=409, detail="У магазина не настроен автоматический parser")
    from app.workers.tasks import sync_store_task

    task = sync_store_task.delay(str(store_id))
    return TaskQueuedResponse(task_id=task.id)


@router.get("/parser-runs", response_model=Page[ParserRunOut])
async def parser_runs(
    session: DbSession,
    _: AdminUser,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page[ParserRunOut]:
    filters = []
    if status_filter:
        filters.append(ParserRun.status == status_filter)
    total = await session.scalar(select(func.count(ParserRun.id)).where(*filters)) or 0
    result = await session.execute(
        select(ParserRun)
        .where(*filters)
        .order_by(ParserRun.started_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return Page[ParserRunOut](
        items=[
            ParserRunOut.model_validate(item, from_attributes=True) for item in result.scalars()
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/audit-logs", response_model=Page[AuditLogOut])
async def audit_logs(
    session: DbSession,
    _: AdminUser,
    action: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> Page[AuditLogOut]:
    filters = [AuditLog.action == action] if action else []
    total = await session.scalar(select(func.count(AuditLog.id)).where(*filters)) or 0
    result = await session.execute(
        select(AuditLog)
        .where(*filters)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return Page[AuditLogOut](
        items=[AuditLogOut.model_validate(item, from_attributes=True) for item in result.scalars()],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/users", response_model=Page[UserOut])
async def admin_users(
    session: DbSession,
    _: AdminUser,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> Page[UserOut]:
    total = await session.scalar(select(func.count(User.id))) or 0
    result = await session.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    )
    items = [
        UserOut(
            id=item.id,
            email=item.email,
            display_name=item.display_name,
            role=item.role,
            is_active=item.is_active,
            is_verified=item.is_verified,
            created_at=item.created_at,
        )
        for item in result.scalars()
    ]
    return Page[UserOut](items=items, total=total, limit=limit, offset=offset)


@router.patch("/users/{user_id}", response_model=UserOut)
async def admin_update_user(
    user_id: UUID, payload: AdminUserUpdate, session: DbSession, request: Request, admin: AdminUser
) -> UserOut:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.id == admin.id and payload.is_active is False:
        raise HTTPException(status_code=400, detail="Нельзя отключить собственный аккаунт")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    await audit(
        session,
        request,
        "admin.user_update",
        "user",
        user.id,
        user_id=admin.id,
        details=payload.model_dump(exclude_unset=True),
    )
    await session.commit()
    return UserOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )
