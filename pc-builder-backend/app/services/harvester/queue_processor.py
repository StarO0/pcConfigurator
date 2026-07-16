from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.entities import CrawlQueueItem, Store
from app.services.harvester.extraction import extract_product
from app.services.harvester.ingest import HarvestResult, ingest_items


async def _robots(client: httpx.AsyncClient, base_url: str) -> RobotFileParser | None:
    parsed = urlparse(base_url)
    try:
        response = await client.get(f"{parsed.scheme}://{parsed.netloc}/robots.txt")
        response.raise_for_status()
    except httpx.HTTPError:
        return None
    parser = RobotFileParser()
    parser.parse(response.text.splitlines())
    return parser


async def process_queue(
    session: AsyncSession, store: Store, *, limit: int = 25
) -> tuple[int, int, HarvestResult]:
    config = store.parser_config or {}
    if not config.get("terms_confirmed", False):
        raise ValueError("Подтвердите правила источника перед серверным обходом")
    now = datetime.now(UTC)
    rows = list(
        (
            await session.execute(
                select(CrawlQueueItem)
                .where(
                    CrawlQueueItem.store_id == store.id,
                    CrawlQueueItem.status == "queued",
                    or_(CrawlQueueItem.not_before.is_(None), CrawlQueueItem.not_before <= now),
                )
                .order_by(CrawlQueueItem.priority, CrawlQueueItem.discovered_at)
                .limit(min(limit, settings.collector_max_pages_per_run))
            )
        ).scalars()
    )
    completed = failed = 0
    aggregate = HarvestResult()
    headers = {
        "User-Agent": settings.collector_user_agent,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
    }
    async with httpx.AsyncClient(
        timeout=settings.collector_request_timeout_seconds,
        follow_redirects=True,
        headers=headers,
    ) as client:
        robots = await _robots(client, store.base_url)
        if robots is None and settings.collector_require_robots:
            raise ValueError("robots.txt недоступен; обход безопасно остановлен")
        for index, row in enumerate(rows):
            row.status = "processing"
            row.attempts += 1
            try:
                if robots and not robots.can_fetch(settings.collector_user_agent, row.url):
                    row.status = "skipped"
                    row.last_error = "robots.txt disallow"
                    failed += 1
                    continue
                response = await client.get(row.url)
                row.last_http_status = response.status_code
                response.raise_for_status()
                item = extract_product(
                    response.text,
                    str(response.url),
                    store.slug,
                    config.get("selectors", {}),
                )
                if item is None:
                    raise ValueError("Карточка товара не найдена")
                imported = await ingest_items(
                    session,
                    [item],
                    store=store,
                    create_products=bool(config.get("create_unmatched_products", True)),
                    auto_accept=True,
                )
                for field in aggregate.__dataclass_fields__:
                    if field == "errors":
                        aggregate.errors.extend(imported.errors)
                    else:
                        setattr(
                            aggregate, field, getattr(aggregate, field) + getattr(imported, field)
                        )
                row.status = "completed"
                row.processed_at = datetime.now(UTC)
                row.last_error = None
                completed += 1
            except Exception as exc:
                row.status = "failed" if row.attempts >= 3 else "queued"
                row.last_error = f"{type(exc).__name__}: {exc}"[:4000]
                failed += 1
            if index + 1 < len(rows):
                await asyncio.sleep(settings.collector_min_delay_seconds)
    await session.flush()
    return completed, failed, aggregate
