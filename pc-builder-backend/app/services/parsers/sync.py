from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import ParserRun, Store
from app.schemas.harvester import HarvestItem
from app.services.harvester.ingest import ingest_items
from app.services.parsers.generic import get_parser


async def sync_store(session: AsyncSession, store: Store, task_id: str | None = None) -> ParserRun:
    run = ParserRun(store_id=store.id, task_id=task_id, status="running")
    session.add(run)
    await session.commit()
    try:
        parser = get_parser(store)
        items = await parser.fetch(store)
        harvested = [HarvestItem.model_validate(item.model_dump()) for item in items]
        imported = await ingest_items(
            session,
            harvested,
            store=store,
            create_products=bool(store.parser_config.get("create_unmatched_products", False)),
            auto_accept=True,
        )
        run.status = "success"
        run.created_count = imported.products_created + imported.offers_created
        run.updated_count = imported.products_updated + imported.offers_updated
        run.skipped_count = imported.pending + imported.duplicates
        run.error_count = imported.rejected
        run.metadata_json = {
            "received": len(items),
            "pending": imported.pending,
            "errors": imported.errors[:100],
        }
        store.last_success_at = datetime.now(UTC)
    except Exception as exc:
        run.status = "failed"
        run.error_count = 1
        run.error_message = f"{type(exc).__name__}: {exc}"[:4000]
        store.last_error_at = datetime.now(UTC)
    finally:
        run.finished_at = datetime.now(UTC)
        await session.commit()
    return run
