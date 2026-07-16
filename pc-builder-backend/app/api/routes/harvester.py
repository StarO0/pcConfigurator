from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import distinct, exists, func, select
from sqlalchemy.orm import selectinload

from app.api.deps import AdminUser, DbSession
from app.models.entities import CrawlQueueItem, HarvestRecord, Offer, ParserRun, Product, Store
from app.schemas.admin import ParserRunOut
from app.schemas.common import MessageResponse, Page
from app.schemas.harvester import (
    CrawlQueueOut,
    EnrichmentRunRequest,
    EnrichmentStatusOut,
    EnrichmentStoreOut,
    HarvesterBatchRequest,
    HarvesterDashboardOut,
    HarvesterImportResponse,
    HarvesterRunDueOut,
    HarvestItem,
    HarvestRecordOut,
    HtmlExtractionRequest,
    HtmlImportRequest,
    QueueUrlsRequest,
)
from app.services.harvester.extraction import extract_product
from app.services.harvester.ingest import ensure_store, ingest_items, queue_urls
from app.services.harvester.queue_processor import process_queue
from app.services.harvester.scheduler import run_due_sources
from app.services.parsers.sync import sync_store

router = APIRouter(prefix="/admin/harvester", tags=["admin-harvester"])


def _response(result) -> HarvesterImportResponse:
    return HarvesterImportResponse(**asdict(result))


def _record_out(record: HarvestRecord) -> HarvestRecordOut:
    payload = record.normalized_payload or {}
    return HarvestRecordOut(
        id=record.id,
        store_id=record.store_id,
        store_slug=record.store.slug,
        product_id=record.product_id,
        source_url=record.source_url,
        external_id=record.external_id,
        status=record.status,
        title=payload.get("title"),
        brand=payload.get("brand"),
        category=payload.get("category"),
        price=Decimal(str(payload["price"])) if payload.get("price") is not None else None,
        currency=payload.get("currency"),
        image_url=payload.get("image_url"),
        match_confidence=record.match_confidence,
        match_method=record.match_method,
        quality_score=record.quality_score,
        error_message=record.error_message,
        discovered_at=record.discovered_at,
        processed_at=record.processed_at,
    )


@router.get("/dashboard", response_model=HarvesterDashboardOut)
async def dashboard(session: DbSession, _: AdminUser) -> HarvesterDashboardOut:
    async def count(model, *filters) -> int:
        return await session.scalar(select(func.count(model.id)).where(*filters)) or 0

    products = await count(Product, Product.is_active.is_(True))
    products_with_images = await count(
        Product,
        Product.is_active.is_(True),
        Product.image_url.is_not(None),
        Product.image_url != "",
    )
    offers = list(
        (
            await session.execute(select(Offer.source_metadata).where(Offer.is_active.is_(True)))
        ).scalars()
    )
    snapshot_offers = sum(1 for metadata in offers if (metadata or {}).get("snapshot"))
    return HarvesterDashboardOut(
        records=await count(HarvestRecord),
        accepted=await count(HarvestRecord, HarvestRecord.status == "accepted"),
        pending=await count(HarvestRecord, HarvestRecord.status == "pending"),
        rejected=await count(HarvestRecord, HarvestRecord.status == "rejected"),
        errors=await count(HarvestRecord, HarvestRecord.status == "error"),
        queued_urls=await count(CrawlQueueItem, CrawlQueueItem.status == "queued"),
        products=products,
        products_with_images=products_with_images,
        image_coverage_percent=round(products_with_images * 100 / products, 2) if products else 0,
        active_offers=await count(Offer, Offer.is_active.is_(True), Offer.in_stock.is_(True)),
        snapshot_offers=snapshot_offers,
        source_count=await count(Store),
    )


@router.get("/enrichment/status", response_model=EnrichmentStatusOut)
async def enrichment_status(session: DbSession, _: AdminUser) -> EnrichmentStatusOut:
    active_products = [Product.is_active.is_(True), Product.status == "active"]
    active_offer = exists(
        select(Offer.id).where(Offer.product_id == Product.id, Offer.is_active.is_(True))
    )
    has_image = Product.image_url.is_not(None) & (Product.image_url != "")
    products = await session.scalar(select(func.count(Product.id)).where(*active_products)) or 0
    products_with_images = (
        await session.scalar(select(func.count(Product.id)).where(*active_products, has_image)) or 0
    )
    products_with_offers = (
        await session.scalar(select(func.count(Product.id)).where(*active_products, active_offer))
        or 0
    )
    products_complete = (
        await session.scalar(
            select(func.count(Product.id)).where(*active_products, has_image, active_offer)
        )
        or 0
    )
    multiple_store_rows = (
        select(Offer.product_id)
        .where(Offer.is_active.is_(True))
        .group_by(Offer.product_id)
        .having(func.count(distinct(Offer.store_id)) >= 2)
        .subquery()
    )
    products_with_multiple_stores = (
        await session.scalar(select(func.count()).select_from(multiple_store_rows)) or 0
    )
    pending_ambiguous = (
        await session.scalar(
            select(func.count(HarvestRecord.id)).where(
                HarvestRecord.status == "pending",
                HarvestRecord.match_method == "ambiguous_variant",
            )
        )
        or 0
    )
    stores = list(
        (
            await session.execute(
                select(Store)
                .where(Store.parser_type.in_(("catalog_acquisition", "catalog_enrichment")))
                .order_by(Store.name)
            )
        ).scalars()
    )
    recent_runs = list(
        (
            await session.execute(
                select(ParserRun)
                .where(ParserRun.store_id.in_([store.id for store in stores]))
                .order_by(ParserRun.started_at.desc())
            )
        ).scalars()
    )
    latest_run_by_store: dict[UUID, ParserRun] = {}
    for run in recent_runs:
        if run.store_id is not None:
            latest_run_by_store.setdefault(run.store_id, run)
    return EnrichmentStatusOut(
        products=products,
        products_with_images=products_with_images,
        products_with_offers=products_with_offers,
        products_complete=products_complete,
        products_with_multiple_stores=products_with_multiple_stores,
        missing_images=max(products - products_with_images, 0),
        missing_offers=max(products - products_with_offers, 0),
        coverage_percent=round(products_complete * 100 / products, 2) if products else 0,
        pending_ambiguous=pending_ambiguous,
        stores=[
            EnrichmentStoreOut(
                id=store.id,
                slug=store.slug,
                name=store.name,
                is_active=store.is_active,
                terms_confirmed=bool((store.parser_config or {}).get("terms_confirmed")),
                discovered_urls=int((store.parser_config or {}).get("discovered_urls", 0)),
                crawl_offset=int((store.parser_config or {}).get("crawl_offset", 0)),
                last_batch=(store.parser_config or {}).get("last_batch", {}),
                last_discovery_batch=(store.parser_config or {}).get("last_discovery_batch", {}),
                last_run_status=(
                    latest_run_by_store[store.id].status
                    if store.id in latest_run_by_store
                    else None
                ),
                last_error_message=(
                    latest_run_by_store[store.id].error_message
                    if store.id in latest_run_by_store
                    else None
                ),
                last_success_at=store.last_success_at,
                last_error_at=store.last_error_at,
            )
            for store in stores
        ],
    )


@router.post("/enrichment/run/{store_id}", response_model=ParserRunOut)
async def run_enrichment_batch(
    store_id: UUID,
    payload: EnrichmentRunRequest,
    session: DbSession,
    _: AdminUser,
) -> ParserRunOut:
    store = await session.get(Store, store_id)
    if store is None or store.parser_type not in {"catalog_acquisition", "catalog_enrichment"}:
        raise HTTPException(status_code=404, detail="Источник наполнения каталога не найден")
    if not payload.terms_confirmed:
        raise HTTPException(
            status_code=409,
            detail="Подтвердите проверку robots.txt и условий выбранного магазина",
        )
    config = dict(store.parser_config or {})
    config.update(
        {
            "terms_confirmed": True,
            "max_pages_per_run": payload.pages,
            "create_unmatched_products": True,
            "require_complete_card": True,
            "enrichment_only": False,
        }
    )
    store.parser_type = "catalog_acquisition"
    store.parser_config = config
    store.is_active = True
    await session.commit()
    run = await sync_store(session, store, task_id="catalog-acquisition-ui")
    return ParserRunOut.model_validate(run, from_attributes=True)


@router.get("/records", response_model=Page[HarvestRecordOut])
async def records(
    session: DbSession,
    _: AdminUser,
    status: str | None = Query(default=None, pattern="^(pending|accepted|rejected|error)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page[HarvestRecordOut]:
    filters = [HarvestRecord.status == status] if status else []
    total = await session.scalar(select(func.count(HarvestRecord.id)).where(*filters)) or 0
    result = await session.execute(
        select(HarvestRecord)
        .options(selectinload(HarvestRecord.store))
        .where(*filters)
        .order_by(HarvestRecord.discovered_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return Page(
        items=[_record_out(item) for item in result.scalars()],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/queue", response_model=Page[CrawlQueueOut])
async def crawl_queue(
    session: DbSession,
    _: AdminUser,
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page[CrawlQueueOut]:
    filters = [CrawlQueueItem.status == status] if status else []
    total = await session.scalar(select(func.count(CrawlQueueItem.id)).where(*filters)) or 0
    rows = (
        await session.execute(
            select(CrawlQueueItem)
            .options(selectinload(CrawlQueueItem.store))
            .where(*filters)
            .order_by(CrawlQueueItem.priority, CrawlQueueItem.discovered_at)
            .offset(offset)
            .limit(limit)
        )
    ).scalars()
    return Page(
        items=[
            CrawlQueueOut(
                id=item.id,
                store_id=item.store_id,
                store_slug=item.store.slug,
                url=item.url,
                status=item.status,
                priority=item.priority,
                attempts=item.attempts,
                not_before=item.not_before,
                last_http_status=item.last_http_status,
                last_error=item.last_error,
                discovered_at=item.discovered_at,
                processed_at=item.processed_at,
            )
            for item in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/browser-import", response_model=HarvesterImportResponse)
async def browser_import(
    payload: HarvesterBatchRequest, session: DbSession, _: AdminUser
) -> HarvesterImportResponse:
    store = await ensure_store(
        session,
        slug=payload.source_slug,
        name=payload.source_name,
        base_url=str(payload.source_base_url),
        terms_confirmed=payload.terms_confirmed,
    )
    items = [item.model_copy(update={"store_slug": store.slug}) for item in payload.items]
    result = await ingest_items(
        session,
        items,
        store=store,
        create_products=payload.create_products,
        auto_accept=payload.auto_accept,
        raw_items=[item.model_dump(mode="json") for item in payload.items],
    )
    await session.commit()
    return _response(result)


@router.post("/extract-preview", response_model=HarvestItem)
async def extraction_preview(payload: HtmlExtractionRequest, _: AdminUser) -> HarvestItem:
    item = extract_product(payload.html, str(payload.url), payload.store_slug, payload.selectors)
    if item is None:
        raise HTTPException(status_code=422, detail="На странице не найдена карточка товара")
    return item


@router.post("/html-import", response_model=HarvesterImportResponse)
async def html_import(
    payload: HtmlImportRequest, session: DbSession, _: AdminUser
) -> HarvesterImportResponse:
    item = extract_product(payload.html, str(payload.url), payload.store_slug, payload.selectors)
    if item is None:
        raise HTTPException(status_code=422, detail="На странице не найдена карточка товара")
    base_url = f"{payload.url.scheme}://{payload.url.host}"
    store = await ensure_store(
        session,
        slug=payload.store_slug,
        name=payload.source_name,
        base_url=base_url,
        terms_confirmed=False,
    )
    result = await ingest_items(
        session,
        [item],
        store=store,
        create_products=payload.create_products,
        auto_accept=payload.auto_accept,
        raw_items=[
            {"html_source_url": str(payload.url), "extracted": item.model_dump(mode="json")}
        ],
    )
    await session.commit()
    return _response(result)


@router.post("/queue", response_model=MessageResponse)
async def add_queue(payload: QueueUrlsRequest, session: DbSession, _: AdminUser) -> MessageResponse:
    store = await session.scalar(select(Store).where(Store.slug == payload.store_slug))
    if store is None:
        raise HTTPException(status_code=404, detail="Источник не найден")
    created, duplicates = await queue_urls(
        session, store, [str(url) for url in payload.urls], payload.priority
    )
    await session.commit()
    return MessageResponse(message=f"В очередь добавлено {created}; дублей {duplicates}")


@router.post("/queue/process/{store_id}", response_model=MessageResponse)
async def process_queued_urls(
    store_id: UUID,
    session: DbSession,
    _: AdminUser,
    limit: int = Query(default=25, ge=1, le=100),
) -> MessageResponse:
    store = await session.get(Store, store_id)
    if store is None or not store.is_active:
        raise HTTPException(status_code=404, detail="Активный источник не найден")
    try:
        completed, failed, imported = await process_queue(session, store, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    await session.commit()
    return MessageResponse(
        message=(
            f"Обработано {completed}; ошибок/повторов {failed}; "
            f"принято {imported.accepted}; ожидает проверки {imported.pending}"
        )
    )


@router.post("/records/{record_id}/approve", response_model=HarvesterImportResponse)
async def approve_record(
    record_id: UUID, session: DbSession, _: AdminUser
) -> HarvesterImportResponse:
    record = await session.scalar(
        select(HarvestRecord)
        .options(selectinload(HarvestRecord.store))
        .where(HarvestRecord.id == record_id)
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Staging-запись не найдена")
    if record.match_method == "ambiguous_variant" and record.product_id is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Совпадение неоднозначно: у вариантов одинаковое название. "
                "Добавьте EAN/MPN или характеристики и импортируйте запись повторно."
            ),
        )
    item = HarvestItem.model_validate(record.normalized_payload)
    result = await ingest_items(
        session,
        [item],
        store=record.store,
        create_products=True,
        auto_accept=True,
        force_accept=True,
    )
    await session.commit()
    return _response(result)


@router.post("/records/{record_id}/reject", response_model=MessageResponse)
async def reject_record(record_id: UUID, session: DbSession, _: AdminUser) -> MessageResponse:
    record = await session.get(HarvestRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Staging-запись не найдена")
    record.status = "rejected"
    record.error_message = "Отклонено администратором"
    await session.commit()
    return MessageResponse(message="Запись отклонена")


@router.post("/run-due", response_model=HarvesterRunDueOut)
async def run_due(session: DbSession, _: AdminUser) -> HarvesterRunDueOut:
    checked, started, skipped, run_ids = await run_due_sources(session)
    return HarvesterRunDueOut(checked=checked, started=started, skipped=skipped, runs=run_ids)
