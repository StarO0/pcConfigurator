from __future__ import annotations

import csv
import io
import os
from decimal import Decimal
from typing import Any

import httpx

from app.models.entities import Store
from app.schemas.products import OfferImportItem
from app.services.parsers.base import StoreParser


def resolve_env(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        name = value[2:-1]
        if name not in os.environ:
            raise ValueError(f"Missing environment variable: {name}")
        return os.environ[name]
    if isinstance(value, dict):
        return {key: resolve_env(item) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_env(item) for item in value]
    return value


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "tak", "available", "in_stock"}


def nested_get(data: dict[str, Any], path: str, default=None):
    current: Any = data
    for key in path.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current


class GenericJSONFeedParser(StoreParser):
    async def fetch(self, store: Store) -> list[OfferImportItem]:
        cfg = resolve_env(store.parser_config)
        headers = cfg.get("headers", {})
        async with httpx.AsyncClient(
            timeout=cfg.get("timeout", 30), follow_redirects=True
        ) as client:
            response = await client.get(cfg["url"], headers=headers)
            response.raise_for_status()
            payload = response.json()
        rows = nested_get(payload, cfg.get("items_path", "items"), [])
        fields = cfg.get("fields", {})
        return [self._map(store, row, fields) for row in rows]

    @staticmethod
    def _map(store: Store, row: dict, fields: dict) -> OfferImportItem:
        def value(name: str, default=None):
            path = fields.get(name, name)
            return nested_get(row, path, default)

        return OfferImportItem(
            product_sku=value("product_sku"),
            ean=value("ean"),
            mpn=value("mpn"),
            title=str(value("title")),
            store_slug=store.slug,
            external_id=str(value("external_id")),
            url=str(value("url")),
            price=Decimal(str(value("price"))),
            shipping_price=Decimal(str(value("shipping_price", 0))),
            currency=str(value("currency", "PLN")),
            in_stock=parse_bool(value("in_stock", True)),
            stock_quantity=value("stock_quantity"),
            condition=str(value("condition", "new")),
        )


class GenericCSVFeedParser(StoreParser):
    async def fetch(self, store: Store) -> list[OfferImportItem]:
        cfg = resolve_env(store.parser_config)
        async with httpx.AsyncClient(
            timeout=cfg.get("timeout", 30), follow_redirects=True
        ) as client:
            response = await client.get(cfg["url"], headers=cfg.get("headers", {}))
            response.raise_for_status()
        reader = csv.DictReader(
            io.StringIO(response.text),
            delimiter=cfg.get("delimiter", ","),
        )
        fields = cfg.get("fields", {})

        def get(row, name, default=None):
            return row.get(fields.get(name, name), default)

        items: list[OfferImportItem] = []
        for row in reader:
            items.append(
                OfferImportItem(
                    product_sku=get(row, "product_sku"),
                    ean=get(row, "ean"),
                    mpn=get(row, "mpn"),
                    title=str(get(row, "title")),
                    store_slug=store.slug,
                    external_id=str(get(row, "external_id")),
                    url=str(get(row, "url")),
                    price=Decimal(str(get(row, "price"))),
                    shipping_price=Decimal(str(get(row, "shipping_price", 0) or 0)),
                    currency=str(get(row, "currency", "PLN")),
                    in_stock=str(get(row, "in_stock", "true")).lower()
                    in {"1", "true", "yes", "tak"},
                    stock_quantity=int(get(row, "stock_quantity"))
                    if get(row, "stock_quantity")
                    else None,
                    condition=str(get(row, "condition", "new")),
                )
            )
        return items


PARSERS: dict[str, type[StoreParser]] = {
    "json": GenericJSONFeedParser,
    "api": GenericJSONFeedParser,
    "csv": GenericCSVFeedParser,
}


def get_parser(store: Store) -> StoreParser:
    parser_class = PARSERS.get(store.parser_type)
    if parser_class is None:
        raise ValueError(f"No parser registered for type {store.parser_type}")
    return parser_class()
