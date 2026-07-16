from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    CrawlQueueItem,
    HarvestRecord,
    Offer,
    PriceHistory,
    Product,
    Store,
)
from app.schemas.harvester import HarvestItem
from app.services.matching import normalize_text, product_matcher
from app.services.spec_normalization import normalize_specs

KNOWN_CATEGORIES = {
    "cpu",
    "motherboard",
    "gpu",
    "ram",
    "storage",
    "psu",
    "case",
    "cooler",
    "monitor",
    "mouse",
    "keyboard",
    "headphones",
    "headset",
    "webcam",
    "ups",
    "speaker",
    "microphone",
    "controller",
    "network",
    "accessory",
    "fan",
    "external-storage",
    "wireless-network-card",
    "wired-network-card",
    "optical-drive",
    "thermal-paste",
    "sound-card",
    "fan-controller",
    "case-accessory",
    "os",
}


@dataclass(slots=True)
class HarvestResult:
    received: int = 0
    accepted: int = 0
    pending: int = 0
    rejected: int = 0
    products_created: int = 0
    products_updated: int = 0
    offers_created: int = 0
    offers_updated: int = 0
    duplicates: int = 0
    errors: list[str] = field(default_factory=list)


def quality_score(item: HarvestItem) -> float:
    score = 30.0  # valid title and URL are mandatory in the schema
    score += 10 if item.brand else 0
    score += 15 if item.category else 0
    score += 15 if item.image_url else 0
    score += 15 if item.specs else 0
    score += 10 if any((item.ean, item.mpn, item.product_sku)) else 0
    score += 5 if item.price is not None else 0
    return min(score, 100.0)


def complete_card_errors(item: HarvestItem) -> list[str]:
    errors: list[str] = []
    if item.price is None:
        errors.append("price")
    if not item.image_url or not str(item.image_url).startswith("https://"):
        errors.append("https_image")
    if not item.category or item.category.lower() not in KNOWN_CATEGORIES:
        errors.append("known_category")
    if not item.brand or item.brand.strip().casefold() == "unknown":
        errors.append("brand")
    ean = re.sub(r"\D", "", item.ean or "")
    has_gtin = 8 <= len(ean) <= 14
    has_mpn = bool(item.brand and item.mpn and item.mpn.strip())
    if not (has_gtin or has_mpn):
        errors.append("gtin_or_brand_mpn")
    return errors


def _fingerprint(store_id: object, item: HarvestItem) -> str:
    identity = item.external_id or str(item.url)
    return hashlib.sha256(f"{store_id}:{identity}".encode()).hexdigest()


async def ensure_store(
    session: AsyncSession,
    *,
    slug: str,
    name: str,
    base_url: str,
    parser_type: str = "browser_snapshot",
    terms_confirmed: bool = False,
) -> Store:
    store = await session.scalar(select(Store).where(Store.slug == slug))
    if store is None:
        store = Store(
            slug=slug,
            name=name,
            base_url=base_url,
            country="PL",
            parser_type=parser_type,
            parser_config={"terms_confirmed": terms_confirmed},
            is_active=True,
        )
        session.add(store)
        await session.flush()
    return store


async def _new_sku(session: AsyncSession, item: HarvestItem) -> str:
    base = item.product_sku or item.ean or item.mpn
    if base:
        candidate = str(base)[:120]
        if await session.scalar(select(Product.id).where(Product.sku == candidate)) is None:
            return candidate
    digest = hashlib.sha256(f"{item.store_slug}:{item.external_id}".encode()).hexdigest()[:16]
    return f"AUTO-{item.store_slug[:30]}-{digest}"[:120]


async def _publish(
    session: AsyncSession,
    store: Store,
    item: HarvestItem,
    product: Product | None,
    result: HarvestResult,
    *,
    force_accept: bool,
) -> Product:
    category = (item.category or "accessory").lower()
    if product is None:
        metadata = item.source_metadata or {}
        gallery = [str(url) for url in metadata.get("gallery_urls", []) if str(url)]
        product = Product(
            category=category,
            brand=item.brand or "Unknown",
            name=item.title[:255],
            normalized_name=normalize_text(item.title),
            sku=await _new_sku(session, item),
            ean=item.ean,
            mpn=item.mpn,
            image_url=str(item.image_url) if item.image_url else None,
            gallery_urls=gallery[:24],
            canonical_source=metadata.get("canonical_source"),
            canonical_id=(
                str(metadata["canonical_id"]) if metadata.get("canonical_id") is not None else None
            ),
            source_url=metadata.get("canonical_url") or str(item.url),
            specs=normalize_specs(category, item.title, item.brand or "Unknown", item.specs),
            quality_score=max(quality_score(item), 50),
            status="active" if item.category or force_accept else "draft",
            is_active=bool(item.category or force_accept),
        )
        session.add(product)
        await session.flush()
        result.products_created += 1
    else:
        changed = False
        metadata = item.source_metadata or {}
        if metadata.get("canonical_source") == "open_icecat":
            canonical_name = item.title[:255]
            if product.name != canonical_name:
                product.name = canonical_name
                product.normalized_name = normalize_text(item.title)
                changed = True
            if item.brand and product.brand != item.brand:
                product.brand = item.brand
                changed = True
            product.canonical_source = "open_icecat"
            product.canonical_id = str(metadata.get("canonical_id") or "") or None
            product.source_url = metadata.get("canonical_url") or product.source_url
            gallery = [str(url) for url in metadata.get("gallery_urls", []) if str(url)]
            if gallery and gallery != (product.gallery_urls or []):
                product.gallery_urls = gallery[:24]
                changed = True
        if item.image_url and str(item.image_url) != product.image_url:
            product.image_url = str(item.image_url)
            changed = True
        if item.ean and not product.ean:
            product.ean = item.ean
            changed = True
        if item.mpn and not product.mpn:
            product.mpn = item.mpn
            changed = True
        normalized_specs = normalize_specs(
            product.category, product.name, product.brand, {**(product.specs or {}), **item.specs}
        )
        if normalized_specs != product.specs:
            product.specs = normalized_specs
            changed = True
        product.quality_score = max(product.quality_score, quality_score(item))
        if changed:
            result.products_updated += 1

    if item.price is None:
        return product
    now = datetime.now(UTC)
    offer = await session.scalar(
        select(Offer).where(Offer.store_id == store.id, Offer.external_id == item.external_id)
    )
    metadata = {
        **item.source_metadata,
        "harvested_at": now.isoformat(),
        "price_kind": item.source_metadata.get("price_kind", "observed"),
    }
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
            source_metadata=metadata,
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
        result.offers_created += 1
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
        offer.source_metadata = metadata
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
            result.offers_updated += 1
        else:
            result.duplicates += 1
    return product


async def ingest_items(
    session: AsyncSession,
    items: list[HarvestItem],
    *,
    store: Store | None = None,
    create_products: bool = True,
    auto_accept: bool = True,
    force_accept: bool = False,
    identity_only_matches: bool = False,
    raw_items: list[dict[str, Any]] | None = None,
) -> HarvestResult:
    result = HarvestResult(received=len(items))
    stores = {entry.slug: entry for entry in (await session.execute(select(Store))).scalars()}
    if store:
        stores[store.slug] = store
    now = datetime.now(UTC)
    for index, item in enumerate(items):
        try:
            item_store = stores.get(item.store_slug)
            if item_store is None or not item_store.is_active:
                result.rejected += 1
                result.errors.append(f"{item.external_id}: source is missing or disabled")
                continue
            fingerprint = _fingerprint(item_store.id, item)
            record = await session.scalar(
                select(HarvestRecord).where(
                    HarvestRecord.store_id == item_store.id,
                    HarvestRecord.fingerprint == fingerprint,
                )
            )
            normalized = item.model_dump(mode="json")
            raw = raw_items[index] if raw_items and index < len(raw_items) else normalized
            if record is None:
                record = HarvestRecord(
                    store_id=item_store.id,
                    source_url=str(item.url),
                    external_id=item.external_id,
                    fingerprint=fingerprint,
                    raw_payload=raw,
                    normalized_payload=normalized,
                )
                session.add(record)
                await session.flush()
            else:
                record.raw_payload = raw
                record.normalized_payload = normalized
                record.source_url = str(item.url)
                result.duplicates += 1

            normalized_match_specs = normalize_specs(
                (item.category or "accessory").lower(),
                item.title,
                item.brand or "Unknown",
                item.specs,
            )
            match = await product_matcher.match(
                session,
                sku=item.product_sku,
                ean=item.ean,
                mpn=item.mpn,
                title=item.title,
                brand=item.brand,
                category=item.category,
                specs=normalized_match_specs,
                minimum_fuzzy_score=75,
            )
            record.match_confidence = match.confidence
            record.match_method = match.method
            record.quality_score = quality_score(item)
            product = match.product
            required_complete = bool(
                (item_store.parser_config or {}).get("require_complete_card")
                or item_store.parser_type == "catalog_acquisition"
            )
            card_errors = complete_card_errors(item) if required_complete else []
            if product is None and create_products and card_errors and not force_accept:
                record.status = "rejected"
                record.processed_at = now
                record.error_message = f"incomplete_card: {', '.join(card_errors)}"
                record.match_method = "quality_gate"
                result.rejected += 1
                result.errors.append(f"{item.external_id}: {record.error_message}")
                continue
            can_create = (
                create_products
                and bool(item.category)
                and (item.category.lower() in KNOWN_CATEGORIES)
                and not card_errors
            )
            accepted_match = product is not None and match.confidence >= 92
            accepted_new = product is None and can_create and record.quality_score >= 65
            if force_accept or (auto_accept and (accepted_match or accepted_new)):
                exact_identity = match.method in {"sku", "ean", "mpn"}
                publish_match = (
                    product
                    if accepted_match and (not identity_only_matches or exact_identity)
                    else None
                )
                publishing_new_product = publish_match is None
                product = await _publish(
                    session,
                    item_store,
                    item,
                    publish_match,
                    result,
                    force_accept=force_accept,
                )
                record.product_id = product.id
                record.status = "accepted"
                record.processed_at = now
                record.error_message = None
                if publishing_new_product:
                    record.match_method = "created"
                    record.match_confidence = 100.0
                result.accepted += 1
            else:
                record.product_id = product.id if product and match.confidence >= 75 else None
                record.status = "pending"
                record.processed_at = None
                result.pending += 1
        except Exception as exc:
            result.errors.append(f"{item.external_id}: {type(exc).__name__}: {exc}")
            result.rejected += 1
    await session.flush()
    return result


async def queue_urls(
    session: AsyncSession, store: Store, urls: list[str], priority: int = 100
) -> tuple[int, int]:
    created = duplicates = 0
    for url in dict.fromkeys(urls):
        digest = hashlib.sha256(url.encode()).hexdigest()
        existing = await session.scalar(
            select(CrawlQueueItem.id).where(
                CrawlQueueItem.store_id == store.id, CrawlQueueItem.url_hash == digest
            )
        )
        if existing:
            duplicates += 1
            continue
        session.add(
            CrawlQueueItem(
                store_id=store.id,
                url=url,
                url_hash=digest,
                priority=priority,
            )
        )
        created += 1
    await session.flush()
    return created, duplicates


async def snapshot_offer_count(session: AsyncSession) -> int:
    return (
        await session.scalar(
            select(func.count(Offer.id)).where(
                Offer.is_active.is_(True),
                Offer.source_metadata["snapshot"].as_boolean().is_(True),
            )
        )
        or 0
    )
