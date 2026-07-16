from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.entities import Offer, PriceHistory, Store, User
from app.schemas.harvester import HarvestItem
from app.services.harvester.ingest import ensure_store, ingest_items

DEMO_STORE_SLUGS = {"demotech", "pc-market", "hardware-hub"}
BACKEND_DIR = Path(__file__).resolve().parents[2]


async def ensure_bootstrap_admin(session: AsyncSession) -> None:
    if not settings.admin_bootstrap_email or not settings.admin_bootstrap_password:
        return
    email = settings.admin_bootstrap_email.lower()
    existing = await session.scalar(select(User).where(User.email == email))
    if existing is None:
        legacy = await session.scalar(
            select(User).where(User.email == "admin@pc.local", User.role == "admin")
        )
        if legacy is not None:
            legacy.email = email
            legacy.password_hash = hash_password(
                settings.admin_bootstrap_password.get_secret_value()
            )
            await session.flush()
            return
        session.add(
            User(
                email=email,
                display_name="Administrator",
                password_hash=hash_password(settings.admin_bootstrap_password.get_secret_value()),
                role="admin",
                is_verified=True,
            )
        )
        await session.flush()


async def seed_starter_snapshot(session: AsyncSession) -> None:
    path = Path(settings.starter_snapshot_path)
    if not path.is_absolute():
        cwd_path = Path.cwd() / path
        backend_path = BACKEND_DIR / path
        path = cwd_path if cwd_path.exists() else backend_path
    if not path.exists():
        raise FileNotFoundError(f"Starter snapshot not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    observed_at = datetime.fromisoformat(payload["observed_at"])

    await session.execute(
        delete(Store).where(
            Store.slug.in_(DEMO_STORE_SLUGS), Store.base_url.like("https://example.com/%")
        )
    )
    await session.flush()

    manual_store = await ensure_store(
        session,
        slug="manual-import",
        name="Ручной импорт",
        base_url="https://local.invalid",
        parser_type="manual",
    )
    manual_store.parser_type = "manual"
    manual_store.parser_config = {
        "local_only": True,
        "terms_confirmed": True,
        "supported_formats": ["csv", "json", "xml", "yml", "html"],
    }
    manual_store.is_active = True

    stores: dict[str, Store] = {}
    for source in payload["sources"]:
        store = await ensure_store(
            session,
            slug=source["slug"],
            name=source["name"],
            base_url=source["base_url"],
            parser_type="browser_snapshot",
        )
        store.parser_type = "browser_snapshot"
        store.parser_config = {
            "snapshot": True,
            "observed_at": payload["observed_at"],
            "read_only": True,
            "terms_confirmed": False,
        }
        store.last_success_at = observed_at
        store.is_active = True
        stores[store.slug] = store

    items: list[HarvestItem] = []
    for raw in payload["items"]:
        source_metadata = {
            "source": "public_category_listing",
            "snapshot": True,
            "observed_at": payload["observed_at"],
            "price_kind": "snapshot",
            "collection_method": "search_index_verified",
            "verification_url": raw["url"],
            "canonical_source": "verified_store_snapshot",
            "canonical_id": f"{raw['store_slug']}:{raw['external_id']}",
            "canonical_url": raw["url"],
            "gallery_urls": [raw["image_url"]],
        }
        items.append(HarvestItem.model_validate({**raw, "source_metadata": source_metadata}))
    for slug, store in stores.items():
        subset = [item for item in items if item.store_slug == slug]
        await ingest_items(
            session,
            subset,
            store=store,
            create_products=True,
            auto_accept=True,
            force_accept=True,
            identity_only_matches=True,
            raw_items=[item.model_dump(mode="json") for item in subset],
        )

    for item in items:
        store = stores[item.store_slug]
        offer = await session.scalar(
            select(Offer).where(Offer.store_id == store.id, Offer.external_id == item.external_id)
        )
        if offer:
            offer.fetched_at = observed_at
            offer.first_seen_at = observed_at
            offer.last_seen_at = observed_at
            history = list(
                (
                    await session.execute(
                        select(PriceHistory).where(PriceHistory.offer_id == offer.id)
                    )
                ).scalars()
            )
            for point in history:
                point.recorded_at = observed_at
    await session.commit()
