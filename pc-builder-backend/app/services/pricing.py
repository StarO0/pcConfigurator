from __future__ import annotations

import itertools
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from app.models.entities import Offer, Product

BasketMode = Literal["cheapest", "fewest_stores", "balanced"]


@dataclass(slots=True)
class BasketResult:
    offers: dict[str, Offer]
    component_price: Decimal
    delivery_price: Decimal
    total_price: Decimal
    store_count: int


def eligible_offers(product: Product, currency: str, limit: int = 4) -> list[Offer]:
    offers = [
        offer
        for offer in product.offers
        if offer.is_active
        and offer.in_stock
        and offer.condition == "new"
        and offer.currency.upper() == currency.upper()
        and offer.store.is_active
    ]
    offers.sort(key=lambda item: item.price + item.shipping_price)
    return offers[:limit]


def best_product_price(product: Product, currency: str) -> Decimal | None:
    offers = eligible_offers(product, currency, limit=1)
    return offers[0].price + offers[0].shipping_price if offers else None


def optimize_basket(
    products: dict[str, Product],
    currency: str,
    mode: BasketMode = "balanced",
    max_store_count: int | None = None,
) -> BasketResult | None:
    categories = list(products)
    offer_lists = [eligible_offers(products[category], currency) for category in categories]
    if any(not offers for offers in offer_lists):
        return None

    best: tuple[Decimal, tuple[Offer, ...], Decimal, Decimal, int] | None = None
    for combination in itertools.product(*offer_lists):
        stores = {offer.store_id for offer in combination}
        store_count = len(stores)
        if max_store_count is not None and store_count > max_store_count:
            continue
        component_price = sum((offer.price for offer in combination), Decimal("0"))
        # One delivery charge per store: use the maximum item delivery charge from that store.
        delivery_by_store: dict[object, Decimal] = {}
        for offer in combination:
            delivery_by_store[offer.store_id] = max(
                delivery_by_store.get(offer.store_id, Decimal("0")), offer.shipping_price
            )
        delivery_price = sum(delivery_by_store.values(), Decimal("0"))
        total = component_price + delivery_price
        if mode == "fewest_stores":
            objective = total + Decimal(store_count * 150)
        elif mode == "balanced":
            objective = total + Decimal(store_count * 20)
        else:
            objective = total
        candidate = (objective, combination, component_price, delivery_price, store_count)
        if best is None or candidate[0] < best[0]:
            best = candidate

    if best is None:
        return None
    _, combination, component_price, delivery_price, store_count = best
    return BasketResult(
        offers=dict(zip(categories, combination, strict=True)),
        component_price=component_price,
        delivery_price=delivery_price,
        total_price=component_price + delivery_price,
        store_count=store_count,
    )


def price_range(
    products: Iterable[Product], currency: str
) -> tuple[Decimal | None, Decimal | None]:
    prices = [price for product in products if (price := best_product_price(product, currency))]
    return (min(prices), max(prices)) if prices else (None, None)
