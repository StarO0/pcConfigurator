from __future__ import annotations

import asyncio

from sqlalchemy import delete, exists, or_, select, update

from app.db.session import AsyncSessionLocal, engine
from app.models.entities import BuildComponent, Offer, Product


async def prune_incomplete_catalog() -> dict[str, int]:
    """Remove legacy cards that do not have both an image and a real offer.

    Products referenced by an existing build are retained for historical integrity,
    but deactivated so they cannot appear in the catalogue or generator.
    """

    async with AsyncSessionLocal() as session:
        active_offer = exists(
            select(Offer.id).where(
                Offer.product_id == Product.id,
                Offer.is_active.is_(True),
                Offer.price > 0,
            )
        )
        protected_by_build = exists(
            select(BuildComponent.id).where(BuildComponent.product_id == Product.id)
        )
        incomplete = or_(
            Product.image_url.is_(None),
            Product.image_url == "",
            ~active_offer,
        )
        deactivated = await session.execute(
            update(Product)
            .where(incomplete, protected_by_build)
            .values(is_active=False, status="legacy_incomplete")
            .execution_options(synchronize_session=False)
        )
        removed = await session.execute(
            delete(Product)
            .where(incomplete, ~protected_by_build)
            .execution_options(synchronize_session=False)
        )
        await session.commit()
        return {
            "removed": int(removed.rowcount or 0),
            "deactivated": int(deactivated.rowcount or 0),
        }


async def main() -> None:
    report = await prune_incomplete_catalog()
    print(f"Catalog quality gate: removed={report['removed']} deactivated={report['deactivated']}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
