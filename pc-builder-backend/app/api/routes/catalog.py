from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import distinct, func, select

from app.api.deps import DbSession
from app.core.config import settings
from app.models.entities import Offer, PriceHistory, Product, Store
from app.schemas.catalog import (
    CatalogSourceOut,
    CatalogStatusOut,
    CategoryCountOut,
    CompatibilityCheckRequest,
    CompatibilityCheckResponse,
)
from app.services.compatibility import compatibility_engine

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/status", response_model=CatalogStatusOut)
async def catalog_status(session: DbSession) -> CatalogStatusOut:
    products = (
        await session.scalar(
            select(func.count(Product.id)).where(
                Product.is_active.is_(True), Product.status == "active"
            )
        )
        or 0
    )
    active_offers = (
        await session.scalar(
            select(func.count(Offer.id)).where(Offer.is_active.is_(True), Offer.in_stock.is_(True))
        )
        or 0
    )
    products_with_offers = (
        await session.scalar(
            select(func.count(distinct(Offer.product_id))).where(
                Offer.is_active.is_(True), Offer.in_stock.is_(True)
            )
        )
        or 0
    )
    products_with_images = (
        await session.scalar(
            select(func.count(Product.id)).where(
                Product.is_active.is_(True),
                Product.status == "active",
                Product.image_url.is_not(None),
                Product.image_url != "",
            )
        )
        or 0
    )
    history = await session.scalar(select(func.count(PriceHistory.id))) or 0
    store_rows = list((await session.execute(select(Store).order_by(Store.name))).scalars())
    sources = [
        CatalogSourceOut(
            slug=store.slug,
            name=store.name,
            mode=store.parser_type,
            enabled=store.is_active,
            configured=(
                bool(settings.ceneo_enabled and settings.ceneo_api_key_value)
                if store.slug == "ceneo"
                else store.parser_type != "manual"
            ),
            last_success_at=store.last_success_at.isoformat() if store.last_success_at else None,
            last_error_at=store.last_error_at.isoformat() if store.last_error_at else None,
        )
        for store in store_rows
    ]
    return CatalogStatusOut(
        products=products,
        products_with_live_offers=products_with_offers,
        active_offers=active_offers,
        stores=len(store_rows),
        price_history_points=history,
        full_catalog_loaded=(
            products > 0 and products_with_offers == products and products_with_images == products
        ),
        sources=sources,
    )


@router.get("/categories", response_model=list[CategoryCountOut])
async def category_counts(session: DbSession) -> list[CategoryCountOut]:
    product_rows = (
        await session.execute(
            select(Product.category, func.count(Product.id))
            .where(Product.is_active.is_(True))
            .group_by(Product.category)
            .order_by(Product.category)
        )
    ).all()
    offer_rows = dict(
        (
            await session.execute(
                select(Product.category, func.count(distinct(Product.id)))
                .join(Offer, Offer.product_id == Product.id)
                .where(Offer.is_active.is_(True), Offer.in_stock.is_(True))
                .group_by(Product.category)
            )
        ).all()
    )
    return [
        CategoryCountOut(
            category=category,
            products=count,
            products_with_offers=offer_rows.get(category, 0),
        )
        for category, count in product_rows
    ]


@router.post("/compatibility", response_model=CompatibilityCheckResponse)
async def check_compatibility(
    payload: CompatibilityCheckRequest, session: DbSession
) -> CompatibilityCheckResponse:
    ids = set(payload.components.values())
    products = list((await session.execute(select(Product).where(Product.id.in_(ids)))).scalars())
    by_id = {product.id: product for product in products}
    missing = [str(product_id) for product_id in ids if product_id not in by_id]
    if missing:
        raise HTTPException(status_code=404, detail={"missing_product_ids": missing})
    components = {
        category: by_id[product_id] for category, product_id in payload.components.items()
    }
    issues = compatibility_engine.validate(components, payload.language)
    cpu = components.get("cpu")
    gpu = components.get("gpu")
    recommended = compatibility_engine.required_psu_w(cpu, gpu) if cpu and gpu else None
    return CompatibilityCheckResponse(
        status=compatibility_engine.status(issues),
        issues=issues,
        estimated_peak_power_w=compatibility_engine.estimated_peak_power_w(components),
        recommended_psu_w=recommended,
    )
