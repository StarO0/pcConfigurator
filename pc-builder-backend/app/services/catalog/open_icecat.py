from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.products import OfferImportItem
from app.services.parsers.catalog_utils import normalize_category


@dataclass(slots=True)
class IcecatProduct:
    icecat_id: str
    title: str
    brand: str
    mpn: str | None
    gtins: list[str]
    category_name: str
    image_url: str
    gallery_urls: list[str] = field(default_factory=list)
    features: dict[str, Any] = field(default_factory=dict)
    source_url: str | None = None
    description: str | None = None


def normalize_gtin(value: str | None) -> str | None:
    digits = re.sub(r"\D", "", value or "")
    return digits if 8 <= len(digits) <= 14 else None


def _localized(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("Value") or value.get("_") or "").strip()
    return str(value or "").strip()


def _feature_values(groups: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if not isinstance(groups, list):
        return result
    for group in groups:
        if not isinstance(group, dict):
            continue
        group_name = _localized((group.get("FeatureGroup") or {}).get("Name"))
        for entry in group.get("Features") or []:
            if not isinstance(entry, dict):
                continue
            name = _localized((entry.get("Feature") or {}).get("Name"))
            if not name:
                continue
            value = entry.get("PresentationValue")
            if value in (None, ""):
                value = entry.get("LocalValue")
            if value in (None, ""):
                value = entry.get("Value")
            if value not in (None, ""):
                result[name] = value
                if group_name:
                    result.setdefault("icecat_feature_groups", {}).setdefault(group_name, {})[
                        name
                    ] = value
    return result


def parse_icecat_payload(payload: dict[str, Any]) -> IcecatProduct | None:
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    info = data.get("GeneralInfo")
    image = data.get("Image")
    if not isinstance(info, dict) or not isinstance(image, dict):
        return None

    image_url = str(image.get("HighPic") or image.get("Pic500x500") or "").strip()
    title = str(info.get("Title") or info.get("ProductName") or "").strip()
    brand = str(info.get("Brand") or "").strip()
    icecat_id = str(info.get("IcecatId") or "").strip()
    if not all((image_url, title, brand, icecat_id)):
        return None

    raw_gtins = info.get("GTIN") or []
    if isinstance(raw_gtins, str):
        raw_gtins = [raw_gtins]
    gtins = list(
        dict.fromkeys(
            normalized for raw in raw_gtins if (normalized := normalize_gtin(str(raw))) is not None
        )
    )
    gallery: list[str] = []
    for entry in data.get("Gallery") or []:
        if not isinstance(entry, dict):
            continue
        url = str(entry.get("Pic") or entry.get("Pic500x500") or "").strip()
        if url.startswith("https://"):
            gallery.append(url)
    gallery = list(dict.fromkeys([image_url, *gallery]))[:24]
    category = _localized((info.get("Category") or {}).get("Name"))
    description = info.get("Description") or {}
    source_url = str(description.get("URL") or "").strip() or None
    summary = info.get("SummaryDescription") or {}
    short_description = str(summary.get("ShortSummaryDescription") or "").strip() or None
    return IcecatProduct(
        icecat_id=icecat_id,
        title=title,
        brand=brand,
        mpn=str(info.get("BrandPartCode") or "").strip() or None,
        gtins=gtins,
        category_name=category,
        image_url=image_url,
        gallery_urls=gallery,
        features=_feature_values(data.get("FeaturesGroups")),
        source_url=source_url,
        description=short_description,
    )


class OpenIcecatClient:
    """Keyless lookup in the brand-authorized Open Icecat catalogue.

    The public ``openIcecat-live`` shop name is not a private credential. Product
    discovery still comes from a shop feed/sitemap; Icecat supplies canonical
    identity, manufacturer imagery and specifications for that GTIN/MPN.
    """

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def lookup(
        self,
        *,
        gtin: str | None = None,
        brand: str | None = None,
        mpn: str | None = None,
    ) -> IcecatProduct | None:
        normalized_gtin = normalize_gtin(gtin)
        if not normalized_gtin and not (brand and mpn):
            return None
        params: dict[str, str] = {
            "shopname": settings.open_icecat_shopname,
            "lang": settings.open_icecat_language,
        }
        if normalized_gtin:
            params["GTIN"] = normalized_gtin
        else:
            params.update({"Brand": str(brand).strip(), "ProductCode": str(mpn).strip()})

        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(
            timeout=settings.open_icecat_timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": settings.collector_user_agent},
        )
        try:
            response = await client.get(settings.open_icecat_live_url, params=params)
            if response.status_code in {400, 404}:
                return None
            response.raise_for_status()
            return parse_icecat_payload(response.json())
        except (httpx.HTTPError, ValueError, TypeError):
            return None
        finally:
            if owns_client:
                await client.aclose()


async def enrich_offer_items(items: list[OfferImportItem]) -> tuple[list[OfferImportItem], int]:
    if not settings.open_icecat_enabled or not items:
        return items, 0
    enriched = 0
    async with httpx.AsyncClient(
        timeout=settings.open_icecat_timeout_seconds,
        follow_redirects=True,
        headers={"User-Agent": settings.collector_user_agent},
    ) as http:
        client = OpenIcecatClient(http)
        for index, item in enumerate(items):
            product = await client.lookup(gtin=item.ean, brand=item.brand, mpn=item.mpn)
            if product is not None:
                store_title = item.title
                item.title = product.title
                item.brand = product.brand
                item.mpn = product.mpn or item.mpn
                item.ean = normalize_gtin(item.ean) or (product.gtins[0] if product.gtins else None)
                item.image_url = product.image_url
                mapped_category = normalize_category(
                    product.category_name,
                    url=str(item.url),
                    title=product.title,
                )
                if mapped_category != "unknown":
                    item.category = mapped_category
                item.specs = {
                    **product.features,
                    **item.specs,
                    "icecat_category": product.category_name,
                    "icecat_description": product.description,
                    "store_title": store_title,
                }
                item.source_metadata.update(
                    {
                        "canonical_source": "open_icecat",
                        "canonical_id": product.icecat_id,
                        "canonical_url": product.source_url,
                        "gallery_urls": product.gallery_urls,
                        "open_icecat_match": True,
                    }
                )
                enriched += 1
            else:
                item.source_metadata["open_icecat_match"] = False
            if index + 1 < len(items) and settings.open_icecat_min_delay_seconds > 0:
                await asyncio.sleep(settings.open_icecat_min_delay_seconds)
    return items, enriched
