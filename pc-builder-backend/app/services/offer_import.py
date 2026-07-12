from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Offer, PriceHistory, Product, Store
from app.schemas.products import OfferImportItem, UnmatchedOffer
from app.services.matching import normalize_text, product_matcher


@dataclass(slots=True)
class ImportResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    unmatched: list[UnmatchedOffer] = field(default_factory=list)
    seen_offer_ids: set[str] = field(default_factory=set)


async def import_offers(
    session: AsyncSession,
    items: list[OfferImportItem],
    *,
    create_unmatched_products: bool = False,
    full_snapshot_store_id=None,
) -> ImportResult:
    result = ImportResult()
    stores_result = await session.execute(select(Store))
    stores = {store.slug: store for store in stores_result.scalars()}
    now = datetime.now(UTC)

    for item in items:
        store = stores.get(item.store_slug)
        if store is None or not store.is_active:
            result.skipped += 1
            result.unmatched.append(
                UnmatchedOffer(
                    external_id=item.external_id, title=item.title, reason="unknown_store"
                )
            )
            continue
        match = await product_matcher.match(
            session,
            sku=item.product_sku,
            ean=item.ean,
            mpn=item.mpn,
            title=item.title,
        )
        product = match.product
        if product is None and create_unmatched_products:
            sku = item.product_sku or f"AUTO-{store.slug}-{item.external_id}"[:120]
            product = Product(
                category="unknown",
                brand="Unknown",
                name=item.title,
                normalized_name=normalize_text(item.title),
                sku=sku,
                ean=item.ean,
                mpn=item.mpn,
                specs={},
                status="draft",
                is_active=False,
            )
            session.add(product)
            await session.flush()
        if product is None:
            result.skipped += 1
            result.unmatched.append(
                UnmatchedOffer(
                    external_id=item.external_id,
                    title=item.title,
                    reason=f"unmatched:{match.confidence:.0f}",
                )
            )
            continue

        offer = await session.scalar(
            select(Offer)
            .options(selectinload(Offer.store))
            .where(Offer.store_id == store.id, Offer.external_id == item.external_id)
        )
        if offer is None:
            offer = Offer(
                product_id=product.id,
                store_id=store.id,
                external_id=item.external_id,
                title_raw=item.title,
                url=str(item.url),
                price=item.price,
                shipping_price=item.shipping_price,
                currency=item.currency,
                in_stock=item.in_stock,
                stock_quantity=item.stock_quantity,
                condition=item.condition,
                fetched_at=now,
                last_seen_at=now,
            )
            session.add(offer)
            await session.flush()
            session.add(
                PriceHistory(
                    offer_id=offer.id,
                    price=offer.price,
                    shipping_price=offer.shipping_price,
                    in_stock=offer.in_stock,
                )
            )
            result.created += 1
        else:
            changed = (
                offer.price != item.price
                or offer.shipping_price != item.shipping_price
                or offer.in_stock != item.in_stock
            )
            offer.product_id = product.id
            offer.title_raw = item.title
            offer.url = str(item.url)
            offer.price = item.price
            offer.shipping_price = item.shipping_price
            offer.currency = item.currency
            offer.in_stock = item.in_stock
            offer.stock_quantity = item.stock_quantity
            offer.condition = item.condition
            offer.fetched_at = now
            offer.last_seen_at = now
            offer.is_active = True
            if changed:
                session.add(
                    PriceHistory(
                        offer_id=offer.id,
                        price=offer.price,
                        shipping_price=offer.shipping_price,
                        in_stock=offer.in_stock,
                    )
                )
                result.updated += 1
            else:
                result.skipped += 1
        result.seen_offer_ids.add(item.external_id)

    if full_snapshot_store_id is not None:
        unseen = await session.execute(
            select(Offer).where(
                Offer.store_id == full_snapshot_store_id,
                Offer.external_id.not_in(result.seen_offer_ids),
                Offer.is_active.is_(True),
            )
        )
        for offer in unseen.scalars():
            offer.in_stock = False
            offer.is_active = False
            offer.fetched_at = now
    return result
