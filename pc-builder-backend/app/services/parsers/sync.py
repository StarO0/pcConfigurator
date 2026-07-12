from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import ParserRun, Store
from app.services.offer_import import import_offers
from app.services.parsers.generic import get_parser


async def sync_store(session: AsyncSession, store: Store, task_id: str | None = None) -> ParserRun:
    run = ParserRun(store_id=store.id, task_id=task_id, status="running")
    session.add(run)
    await session.commit()
    try:
        parser = get_parser(store)
        items = await parser.fetch(store)
        imported = await import_offers(
            session,
            items,
            full_snapshot_store_id=store.id if store.parser_config.get("full_snapshot") else None,
        )
        run.status = "success"
        run.created_count = imported.created
        run.updated_count = imported.updated
        run.skipped_count = imported.skipped
        run.error_count = len(imported.unmatched)
        run.metadata_json = {
            "received": len(items),
            "unmatched": [item.model_dump() for item in imported.unmatched[:100]],
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
