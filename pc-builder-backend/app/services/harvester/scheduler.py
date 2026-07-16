from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.entities import Store
from app.services.parsers.sync import sync_store

AUTOMATIC_PARSERS = {
    "json",
    "csv",
    "xml",
    "yml",
    "api",
    "html_selector",
    "jsonld_sitemap",
    "catalog_enrichment",
    "catalog_acquisition",
}


async def run_due_sources(session: AsyncSession) -> tuple[int, int, int, list]:
    stores = list(
        (
            await session.execute(
                select(Store).where(
                    Store.is_active.is_(True), Store.parser_type.in_(AUTOMATIC_PARSERS)
                )
            )
        ).scalars()
    )
    checked = len(stores)
    started = skipped = 0
    run_ids = []
    now = datetime.now(UTC)
    for store in stores:
        config = store.parser_config or {}
        if not config.get("terms_confirmed", False):
            skipped += 1
            continue
        every_minutes = max(int(config.get("schedule_minutes", 360)), 15)
        attempts = [
            value.replace(tzinfo=UTC) if value.tzinfo is None else value
            for value in (store.last_success_at, store.last_error_at)
            if value is not None
        ]
        last = max(attempts, default=None)
        if last and last + timedelta(minutes=every_minutes) > now:
            skipped += 1
            continue
        run = await sync_store(session, store, task_id="local-scheduler")
        run_ids.append(run.id)
        started += 1
    return checked, started, skipped, run_ids


async def scheduler_loop() -> None:
    while True:
        try:
            async with AsyncSessionLocal() as session:
                await run_due_sources(session)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Individual runs already persist their error. The loop must survive a bad source.
            pass
        await asyncio.sleep(max(settings.harvester_scheduler_interval_seconds, 60))
