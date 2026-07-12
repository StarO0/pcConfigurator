import asyncio

from app.core.config import settings
from app.db.base import Base
from app.db.seed import seed_demo_data
from app.db.session import AsyncSessionLocal, engine


async def main() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    if settings.seed_demo_data:
        async with AsyncSessionLocal() as session:
            await seed_demo_data(session)


if __name__ == "__main__":
    asyncio.run(main())
