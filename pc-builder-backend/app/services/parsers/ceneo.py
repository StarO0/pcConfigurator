from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.models.entities import Store
from app.schemas.products import OfferImportItem
from app.services.parsers.base import StoreParser
from app.services.parsers.catalog_utils import decimal_value, normalize_category


class CeneoPartnerParser(StoreParser):
    AUTH_URL = "https://partnerzyapi.ceneo.pl/AuthorizationService.svc/GetToken"
    SERVICES = {
        "partner": "https://partnerzyapi.ceneo.pl/PartnerServiceV2.svc",
        "premium": "https://partnerzyapi.ceneo.pl/PartnerServicePremium.svc",
    }

    async def fetch(self, store: Store) -> list[OfferImportItem]:
        key = settings.ceneo_api_key_value
        if not settings.ceneo_enabled or not key:
            raise RuntimeError("Ceneo is disabled: set CENEO_ENABLED and CENEO_API_KEY")
        async with httpx.AsyncClient(
            timeout=settings.collector_request_timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": settings.collector_user_agent, "Accept": "application/json"},
        ) as client:
            token = await self._token(client, key)
            found: dict[str, OfferImportItem] = {}
            for query in settings.ceneo_queries:
                for page in range(settings.ceneo_max_pages_per_query):
                    rows = await self._search(client, token, query, page)
                    if not rows:
                        break
                    for row in rows:
                        item = self._item(store.slug, row)
                        if item:
                            found[item.external_id] = item
                    if len(rows) < settings.ceneo_search_page_size:
                        break
                    await asyncio.sleep(0.2)
            return list(found.values())

    @staticmethod
    async def _token(client: httpx.AsyncClient, key: str) -> str:
        response = await client.get(
            CeneoPartnerParser.AUTH_URL,
            params={"grantType": "'client_credentials'"},
            headers={"Authorization": f"Basic {key}"},
        )
        response.raise_for_status()
        token = response.headers.get("access_token")
        if not token:
            payload = response.json()
            token = payload.get("access_token") if isinstance(payload, dict) else None
        if not token:
            raise RuntimeError("Ceneo did not return access_token")
        return token

    @staticmethod
    def _rows(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            return []
        value = payload.get("value") or payload.get("results") or payload.get("d") or []
        if isinstance(value, dict):
            value = value.get("results") or value.get("value") or []
        return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []

    async def _search(
        self, client: httpx.AsyncClient, token: str, query: str, page: int
    ) -> list[dict[str, Any]]:
        base = self.SERVICES[settings.ceneo_service]
        response = await client.get(
            f"{base}/GetProducts",
            params={
                "searchText": f"'{query.replace(chr(39), chr(39) * 2)}'",
                "pageSize": settings.ceneo_search_page_size,
                "pageIndex": page,
                "$format": "json",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return self._rows(response.json())

    @staticmethod
    def _item(store_slug: str, row: dict[str, Any]) -> OfferImportItem | None:
        product_id = row.get("Id") or row.get("id")
        name = row.get("Name") or row.get("name")
        price = decimal_value(row.get("LowestPrice") or row.get("lowestPrice"))
        if product_id is None or not name or price is None:
            return None
        url = str(row.get("Url") or row.get("url") or f"https://www.ceneo.pl/{product_id}")
        if settings.ceneo_partner_id and "#pid=" not in url:
            url = f"{url}#pid={quote(settings.ceneo_partner_id)}"
        category_value = row.get("Category") or row.get("Categories")
        if isinstance(category_value, list):
            category_value = category_value[0] if category_value else None
        category_name = (
            category_value.get("Name") if isinstance(category_value, dict) else category_value
        )
        category = normalize_category(str(category_name or ""), url=url, title=str(name))
        shops = int(row.get("Shops") or 0)
        highest = decimal_value(row.get("HighestPrice"))
        previous = decimal_value(row.get("PreviousPrice"))
        return OfferImportItem(
            title=str(name),
            store_slug=store_slug,
            external_id=str(product_id),
            url=url,
            price=price,
            currency="PLN",
            in_stock=shops > 0,
            brand=row.get("ManufacturerName"),
            category=category if category != "unknown" else None,
            image_url=row.get("ThumbnailUrl") or row.get("MediumThumbnailUrl"),
            source_metadata={
                "source": "ceneo_affiliate_api",
                "aggregate": True,
                "shops_count": shops,
                "highest_price": str(highest) if highest else None,
                "previous_price": str(previous) if previous else None,
            },
        )
