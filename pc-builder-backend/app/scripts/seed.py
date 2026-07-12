import asyncio

from app.core.config import settings
from app.db.seed import seed_demo_data
from app.db.session import AsyncSessionLocal, engine


async def main() -> None:
    if settings.seed_demo_data:
        async with AsyncSessionLocal() as session:
            await seed_demo_data(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
