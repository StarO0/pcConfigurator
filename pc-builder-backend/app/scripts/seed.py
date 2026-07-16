import asyncio

from app.core.config import settings
from app.db.seed import seed_demo_data
from app.db.session import AsyncSessionLocal, engine
from app.db.starter_snapshot import ensure_bootstrap_admin, seed_starter_snapshot
from app.services.parsers.source_seed import seed_source_stores


async def main() -> None:
    async with AsyncSessionLocal() as session:
        if settings.seed_demo_data:
            await seed_demo_data(session)
        elif settings.starter_snapshot_enabled:
            await seed_starter_snapshot(session)
        await ensure_bootstrap_admin(session)
        await session.commit()
        await seed_source_stores(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
