from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal, engine
from app.models.entities import Product
from app.services.spec_normalization import normalize_specs


async def normalize_catalog(*, dry_run: bool = False, batch_size: int = 250) -> dict[str, int]:
    scanned = 0
    changed = 0
    async with AsyncSessionLocal() as session:
        total = await session.scalar(select(func.count(Product.id))) or 0
        for offset in range(0, total, batch_size):
            result = await session.execute(
                select(Product).order_by(Product.id).offset(offset).limit(batch_size)
            )
            for product in result.scalars():
                scanned += 1
                normalized = normalize_specs(
                    product.category, product.name, product.brand, product.specs or {}
                )
                if normalized != product.specs:
                    changed += 1
                    if not dry_run:
                        product.specs = normalized
            if not dry_run:
                await session.commit()
        return {"scanned": scanned, "changed": changed}


async def run(args: argparse.Namespace) -> None:
    try:
        print(await normalize_catalog(dry_run=args.dry_run, batch_size=args.batch_size))
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize product specifications")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=250)
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
