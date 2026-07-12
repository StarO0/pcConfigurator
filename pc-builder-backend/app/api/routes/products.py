from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.entities import FavoriteProduct, Offer, PriceHistory, Product
from app.schemas.products import (
    FavoriteResponse,
    PriceHistoryResponse,
    PricePointOut,
    ProductListResponse,
    ProductOut,
)
from app.services.serializers import product_to_schema

router = APIRouter(prefix="/products", tags=["products"])

PRODUCT_LOAD = (
    selectinload(Product.offers).selectinload(Offer.store),
    selectinload(Product.benchmarks),
)


@router.get("/categories", response_model=list[str])
async def categories(session: DbSession) -> list[str]:
    result = await session.execute(
        select(Product.category)
        .where(Product.is_active.is_(True), Product.status == "active")
        .distinct()
        .order_by(Product.category)
    )
    return list(result.scalars())


@router.get("/brands", response_model=list[str])
async def brands(session: DbSession, category: str | None = None) -> list[str]:
    query = select(Product.brand).where(Product.is_active.is_(True), Product.status == "active")
    if category:
        query = query.where(Product.category == category)
    result = await session.execute(query.distinct().order_by(Product.brand))
    return list(result.scalars())


@router.get("", response_model=ProductListResponse)
async def list_products(
    session: DbSession,
    category: str | None = None,
    search: str | None = Query(default=None, min_length=2, max_length=200),
    brand: list[str] = Query(default=[]),
    currency: str = Query(default="PLN", min_length=3, max_length=3),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    in_stock: bool = True,
    socket: str | None = None,
    ram_type: str | None = None,
    min_capacity_gb: int | None = Query(default=None, ge=0),
    min_performance: float | None = Query(default=None, ge=0),
    sort: str = Query(default="name", pattern="^(name|price|performance|newest)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ProductListResponse:
    currency = currency.upper()
    offer_filters = [
        Offer.product_id == Product.id,
        Offer.currency == currency,
        Offer.is_active.is_(True),
    ]
    if in_stock:
        offer_filters.append(Offer.in_stock.is_(True))
    min_offer_price = (
        select(func.min(Offer.price + Offer.shipping_price))
        .where(*offer_filters)
        .correlate(Product)
        .scalar_subquery()
    )
    filters = [Product.is_active.is_(True), Product.status == "active"]
    if category:
        filters.append(Product.category == category)
    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Product.name.ilike(term),
                Product.brand.ilike(term),
                Product.sku.ilike(term),
                Product.mpn.ilike(term),
            )
        )
    if brand:
        filters.append(Product.brand.in_(brand))
    if in_stock:
        filters.append(exists(select(1).where(*offer_filters)))
    if min_price is not None:
        filters.append(min_offer_price >= min_price)
    if max_price is not None:
        filters.append(min_offer_price <= max_price)
    if socket:
        filters.append(Product.specs["socket"].as_string() == socket)
    if ram_type:
        filters.append(Product.specs["ram_type"].as_string() == ram_type)
    if min_capacity_gb is not None:
        filters.append(Product.specs["capacity_gb"].as_integer() >= min_capacity_gb)
    if min_performance is not None:
        filters.append(Product.performance_score >= min_performance)

    total = await session.scalar(select(func.count(Product.id)).where(*filters)) or 0
    query = select(Product).options(*PRODUCT_LOAD).where(*filters)
    if sort == "price":
        query = query.order_by(min_offer_price.asc(), Product.name.asc())
    elif sort == "performance":
        query = query.order_by(Product.performance_score.desc(), min_offer_price.asc())
    elif sort == "newest":
        query = query.order_by(Product.release_date.desc().nullslast(), Product.name.asc())
    else:
        query = query.order_by(Product.category, Product.brand, Product.name)
    result = await session.execute(query.offset(offset).limit(limit))
    return ProductListResponse(
        items=[product_to_schema(product) for product in result.scalars().unique()],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/favorites/me", response_model=ProductListResponse)
async def favorite_products(
    session: DbSession,
    user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ProductListResponse:
    total = (
        await session.scalar(
            select(func.count(FavoriteProduct.id)).where(FavoriteProduct.user_id == user.id)
        )
        or 0
    )
    result = await session.execute(
        select(Product)
        .join(FavoriteProduct, FavoriteProduct.product_id == Product.id)
        .options(*PRODUCT_LOAD)
        .where(FavoriteProduct.user_id == user.id)
        .order_by(FavoriteProduct.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return ProductListResponse(
        items=[product_to_schema(item) for item in result.scalars().unique()],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: UUID, session: DbSession) -> ProductOut:
    result = await session.execute(
        select(Product)
        .options(*PRODUCT_LOAD)
        .where(Product.id == product_id, Product.is_active.is_(True))
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return product_to_schema(product)


@router.post("/{product_id}/favorite", response_model=FavoriteResponse)
async def add_favorite(product_id: UUID, session: DbSession, user: CurrentUser) -> FavoriteResponse:
    if await session.get(Product, product_id) is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    existing = await session.scalar(
        select(FavoriteProduct).where(
            FavoriteProduct.user_id == user.id,
            FavoriteProduct.product_id == product_id,
        )
    )
    if existing is None:
        session.add(FavoriteProduct(user_id=user.id, product_id=product_id))
        await session.commit()
    return FavoriteResponse(product_id=product_id, favorite=True)


@router.delete("/{product_id}/favorite", response_model=FavoriteResponse)
async def remove_favorite(
    product_id: UUID, session: DbSession, user: CurrentUser
) -> FavoriteResponse:
    favorite = await session.scalar(
        select(FavoriteProduct).where(
            FavoriteProduct.user_id == user.id,
            FavoriteProduct.product_id == product_id,
        )
    )
    if favorite:
        await session.delete(favorite)
        await session.commit()
    return FavoriteResponse(product_id=product_id, favorite=False)


@router.get("/offers/{offer_id}/history", response_model=PriceHistoryResponse)
async def offer_price_history(
    offer_id: UUID,
    session: DbSession,
    days: int = Query(default=90, ge=1, le=730),
) -> PriceHistoryResponse:
    offer = await session.get(Offer, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Предложение не найдено")
    result = await session.execute(
        select(PriceHistory)
        .where(
            PriceHistory.offer_id == offer_id,
            PriceHistory.recorded_at >= datetime.now(UTC) - timedelta(days=days),
        )
        .order_by(PriceHistory.recorded_at)
    )
    return PriceHistoryResponse(
        offer_id=offer_id,
        points=[
            PricePointOut(
                price=item.price,
                shipping_price=item.shipping_price,
                in_stock=item.in_stock,
                recorded_at=item.recorded_at,
            )
            for item in result.scalars()
        ],
    )
