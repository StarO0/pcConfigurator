from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Build, BuildRevision
from app.services.serializers import build_to_schema


async def create_build_revision(
    session: AsyncSession,
    build: Build,
    reason: str,
) -> None:
    current_revision = await session.scalar(
        select(func.max(BuildRevision.revision)).where(BuildRevision.build_id == build.id)
    )
    snapshot = build_to_schema(build).model_dump(mode="json")
    session.add(
        BuildRevision(
            build_id=build.id,
            revision=int(current_revision or 0) + 1,
            snapshot=snapshot,
            reason=reason,
        )
    )


def recalculate_build_totals(build: Build) -> None:
    component_price = sum(
        (
            component.selected_offer.price * component.quantity
            for component in build.components
            if component.selected_offer is not None
        ),
        Decimal("0"),
    )
    shipping_by_store: dict[object, Decimal] = {}
    for component in build.components:
        offer = component.selected_offer
        if offer is None:
            continue
        shipping_by_store[offer.store_id] = max(
            shipping_by_store.get(offer.store_id, Decimal("0")),
            offer.shipping_price,
        )
    build.delivery_price = sum(shipping_by_store.values(), Decimal("0"))
    build.total_price = component_price + build.delivery_price
    build.store_count = len(shipping_by_store)
