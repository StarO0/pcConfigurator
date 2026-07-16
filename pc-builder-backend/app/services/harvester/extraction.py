from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal
from typing import Any
from urllib.parse import urljoin
from xml.etree import ElementTree

from bs4 import BeautifulSoup, Tag

from app.schemas.harvester import HarvestItem
from app.services.parsers.catalog_utils import bool_stock, decimal_value, fold, normalize_category


def _objects(payload: Any) -> list[dict[str, Any]]:
    values = payload if isinstance(payload, list) else [payload]
    result: list[dict[str, Any]] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        graph = value.get("@graph")
        if isinstance(graph, list):
            result.extend(item for item in graph if isinstance(item, dict))
        else:
            result.append(value)
    return result


def _typed(item: dict[str, Any], wanted: str) -> bool:
    kind = item.get("@type")
    values = kind if isinstance(kind, list) else [kind]
    return any(str(value).rstrip("/").rsplit("/", 1)[-1] == wanted for value in values)


def _first(value: Any) -> Any:
    return value[0] if isinstance(value, list) and value else value


def decimal_price(value: Any) -> Decimal | None:
    return decimal_value(value)


def _selector_value(soup: BeautifulSoup, definition: Any) -> str | None:
    if isinstance(definition, str):
        selector, attribute = definition, None
    elif isinstance(definition, dict):
        selector = str(definition.get("selector") or "")
        attribute = definition.get("attribute") or definition.get("attr")
    else:
        return None
    node = soup.select_one(selector) if selector else None
    if not node:
        return None
    value = node.get(str(attribute)) if attribute else node.get_text(" ", strip=True)
    return str(value).strip() if value else None


def _meta(soup: BeautifulSoup, *names: str) -> str | None:
    for name in names:
        node = soup.find("meta", attrs={"property": name}) or soup.find(
            "meta", attrs={"name": name}
        )
        if node and node.get("content"):
            return str(node["content"]).strip()
    return None


def _table_specs(soup: BeautifulSoup) -> dict[str, Any]:
    specs: dict[str, Any] = {}
    for row in soup.select("table tr, dl"):
        if not isinstance(row, Tag):
            continue
        cells = row.select(":scope > th, :scope > td, :scope > dt, :scope > dd")
        if len(cells) < 2:
            continue
        key = re.sub(r"\s+", " ", cells[0].get_text(" ", strip=True)).strip(": ")
        value = re.sub(r"\s+", " ", cells[1].get_text(" ", strip=True)).strip()
        if key and value and len(key) <= 120 and len(value) <= 1000:
            specs[key] = value
    return specs


def extract_product(
    html: str,
    url: str,
    store_slug: str,
    selectors: dict[str, Any] | None = None,
) -> HarvestItem | None:
    soup = BeautifulSoup(html, "html.parser")
    objects: list[dict[str, Any]] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text("", strip=True)
        if not raw:
            continue
        try:
            objects.extend(_objects(json.loads(raw.strip().rstrip(";"))))
        except (json.JSONDecodeError, TypeError):
            continue
    product = next((item for item in objects if _typed(item, "Product")), {})
    offer = _first(product.get("offers")) or {}
    if isinstance(offer, dict):
        nested = _first(offer.get("offers"))
        if isinstance(nested, dict):
            offer = {**offer, **nested}
    else:
        offer = {}

    selected = selectors or {}
    title = _selector_value(soup, selected.get("title")) or str(product.get("name") or "").strip()
    title = title or _meta(soup, "og:title", "twitter:title") or ""
    if not title:
        heading = soup.select_one("h1")
        title = heading.get_text(" ", strip=True) if heading else ""
    if len(title.strip()) < 2:
        return None

    price_raw = _selector_value(soup, selected.get("price"))
    price = decimal_price(price_raw or offer.get("price") or offer.get("lowPrice"))
    currency = (
        _selector_value(soup, selected.get("currency"))
        or offer.get("priceCurrency")
        or _meta(soup, "product:price:currency")
        or "PLN"
    )
    brand_value = product.get("brand")
    brand = brand_value.get("name") if isinstance(brand_value, dict) else brand_value
    brand = _selector_value(soup, selected.get("brand")) or (str(brand).strip() if brand else None)
    category_raw = _selector_value(soup, selected.get("category")) or product.get("category")
    category = normalize_category(category_raw, url=url, title=title)
    image_value = _first(product.get("image"))
    if isinstance(image_value, dict):
        image_value = image_value.get("url") or image_value.get("contentUrl")
    image = (
        _selector_value(soup, selected.get("image"))
        or (str(image_value).strip() if image_value else None)
        or _meta(soup, "og:image", "twitter:image")
    )
    ean = product.get("gtin13") or product.get("gtin14") or product.get("gtin")
    mpn = product.get("mpn")
    sku = product.get("sku")
    external = _selector_value(soup, selected.get("external_id")) or str(
        sku or ean or mpn or hashlib.sha256(url.encode()).hexdigest()[:32]
    )
    specs = _table_specs(soup)
    additional = product.get("additionalProperty") or []
    if isinstance(additional, dict):
        additional = [additional]
    for entry in additional:
        if isinstance(entry, dict) and entry.get("name") and entry.get("value") is not None:
            specs[str(entry["name"])] = entry["value"]
    folded_specs = {fold(str(key)): value for key, value in specs.items()}
    if not mpn:
        mpn = next(
            (
                folded_specs[key]
                for key in ("kod producenta", "numer katalogowy producenta", "part number", "mpn")
                if folded_specs.get(key)
            ),
            None,
        )
    if not ean:
        ean = next(
            (folded_specs[key] for key in ("ean", "kod ean", "gtin") if folded_specs.get(key)),
            None,
        )
    availability = _selector_value(soup, selected.get("availability")) or offer.get("availability")
    resolved_image = urljoin(url, image) if image else None
    resolved_offer_url = urljoin(url, str(offer.get("url") or url))
    return HarvestItem(
        product_sku=str(sku) if sku else None,
        ean=str(ean) if ean else None,
        mpn=str(mpn) if mpn else None,
        title=title.strip(),
        store_slug=store_slug,
        external_id=external,
        url=resolved_offer_url,
        price=price,
        currency=str(currency)[:3].upper(),
        in_stock=bool_stock(availability) if availability is not None else True,
        brand=brand,
        category=category if category != "unknown" else None,
        image_url=resolved_image,
        specs=specs,
        source_metadata={
            "source": "html_jsonld" if product else "html_selectors",
            "extracted_fields": sorted(selected),
        },
    )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _xml_value(node: ElementTree.Element, names: list[str]) -> str | None:
    wanted = {name.lower() for name in names}
    for child in node.iter():
        if _local_name(child.tag) in wanted and child.text and child.text.strip():
            return child.text.strip()
    return None


def _mapped_xml_value(
    node: ElementTree.Element,
    fields: dict[str, str],
    name: str,
    aliases: list[str],
) -> str | None:
    return _xml_value(node, [fields.get(name, name), *aliases])


def parse_xml_feed(
    xml: str | bytes,
    store_slug: str,
    field_map: dict[str, str] | None = None,
) -> list[HarvestItem]:
    root = ElementTree.fromstring(xml)
    fields = field_map or {}
    nodes = [node for node in root.iter() if _local_name(node.tag) in {"offer", "item", "product"}]
    items: list[HarvestItem] = []
    for node in nodes:
        title = _mapped_xml_value(node, fields, "title", ["name", "product_name"])
        url = _mapped_xml_value(node, fields, "url", ["link", "producturl"])
        if not title or not url:
            continue
        external = (
            node.attrib.get("id")
            or _mapped_xml_value(node, fields, "external_id", ["id", "sku", "code"])
            or hashlib.sha256(url.encode()).hexdigest()[:32]
        )
        category_raw = _mapped_xml_value(node, fields, "category", ["categoryname", "type"])
        category = normalize_category(category_raw, url=url, title=title)
        items.append(
            HarvestItem(
                product_sku=_mapped_xml_value(node, fields, "product_sku", ["sku", "code"]),
                ean=_mapped_xml_value(node, fields, "ean", ["gtin", "barcode"]),
                mpn=_mapped_xml_value(node, fields, "mpn", ["manufacturerpartnumber"]),
                title=title,
                store_slug=store_slug,
                external_id=str(external),
                url=url,
                price=decimal_price(_mapped_xml_value(node, fields, "price", ["saleprice"])),
                shipping_price=decimal_price(
                    _mapped_xml_value(node, fields, "shipping_price", ["deliveryprice"])
                )
                or Decimal("0"),
                currency=(_mapped_xml_value(node, fields, "currency", ["currencyid"]) or "PLN")[
                    :3
                ].upper(),
                in_stock=bool_stock(
                    _mapped_xml_value(
                        node, fields, "availability", ["available", "stock", "instock"]
                    )
                ),
                brand=_mapped_xml_value(node, fields, "brand", ["vendor", "manufacturer"]),
                category=category if category != "unknown" else None,
                image_url=_mapped_xml_value(
                    node, fields, "image_url", ["picture", "image", "imageurl"]
                ),
                source_metadata={"source": "xml_yml"},
            )
        )
    return items
