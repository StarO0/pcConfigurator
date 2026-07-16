from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.models.entities import Store
from app.schemas.products import OfferImportItem
from app.services.harvester.extraction import extract_product
from app.services.parsers.base import StoreParser
from app.services.parsers.catalog_utils import bool_stock, decimal_value, normalize_category

CACHE_DIR = Path("data/harvester-cache")


async def _get_with_retry(client: httpx.AsyncClient, url: str) -> httpx.Response:
    last_response: httpx.Response | None = None
    for attempt in range(3):
        response = await client.get(url)
        last_response = response
        if response.status_code not in {429, 500, 502, 503, 504}:
            response.raise_for_status()
            return response
        if attempt < 2:
            retry_after = response.headers.get("Retry-After", "")
            delay = float(retry_after) if retry_after.replace(".", "", 1).isdigit() else 2**attempt
            await asyncio.sleep(min(max(delay, settings.collector_min_delay_seconds), 60))
    assert last_response is not None
    last_response.raise_for_status()
    return last_response


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


def parse_jsonld_offer(html: str, url: str, store_slug: str) -> OfferImportItem | None:
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
    product = next((item for item in objects if _typed(item, "Product")), None)
    if product is None:
        return None
    offer = _first(product.get("offers")) or {}
    if not isinstance(offer, dict):
        return None
    nested = _first(offer.get("offers"))
    if isinstance(nested, dict):
        offer = {**offer, **nested}
    name = str(product.get("name") or "").strip()
    price = decimal_value(offer.get("price") or offer.get("lowPrice"))
    if not name or price is None:
        return None
    brand_value = product.get("brand")
    brand = brand_value.get("name") if isinstance(brand_value, dict) else brand_value
    image_value = _first(product.get("image"))
    if isinstance(image_value, dict):
        image_value = image_value.get("url") or image_value.get("contentUrl")
    category = normalize_category(product.get("category"), url=url, title=name)
    ean = product.get("gtin13") or product.get("gtin14") or product.get("gtin")
    mpn = product.get("mpn")
    sku = product.get("sku")
    external = sku or ean or mpn or hashlib.sha256(url.encode()).hexdigest()[:32]
    high_price = decimal_value(offer.get("highPrice"))
    shops_count = offer.get("offerCount")
    return OfferImportItem(
        product_sku=str(sku) if sku else None,
        ean=str(ean) if ean else None,
        mpn=str(mpn) if mpn else None,
        title=name,
        store_slug=store_slug,
        external_id=str(external),
        url=urljoin(url, str(offer.get("url") or url)),
        price=price,
        currency=str(offer.get("priceCurrency") or "PLN")[:3].upper(),
        in_stock=bool_stock(offer.get("availability")),
        brand=str(brand).strip() if brand else None,
        category=category if category != "unknown" else None,
        image_url=urljoin(url, str(image_value)) if image_value else None,
        specs={"source_category": product.get("category")} if product.get("category") else {},
        source_metadata={
            "source": "jsonld",
            "aggregate": _typed(offer, "AggregateOffer"),
            "highest_price": str(high_price) if high_price else None,
            "shops_count": int(shops_count) if str(shops_count or "").isdigit() else None,
        },
    )


class JsonLdSitemapParser(StoreParser):
    async def fetch(self, store: Store) -> list[OfferImportItem]:
        config = dict(store.parser_config or {})
        if "sitemap_urls" in config:
            sitemap_urls = config.get("sitemap_urls") or []
        else:
            sitemap_urls = [f"{store.base_url.rstrip('/')}/sitemap.xml"]
        if isinstance(sitemap_urls, str):
            sitemap_urls = [sitemap_urls]
        discovery_urls = config.get("discovery_urls") or []
        if isinstance(discovery_urls, str):
            discovery_urls = [discovery_urls]
        headers = {
            "User-Agent": settings.collector_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.5",
        }
        async with httpx.AsyncClient(
            timeout=settings.collector_request_timeout_seconds,
            follow_redirects=True,
            headers=headers,
        ) as client:
            robots = await self._robots(client, store.base_url)
            if robots is None and settings.collector_require_robots:
                raise RuntimeError(f"robots.txt unavailable for {store.slug}")
            cache_hours = max(int(config.get("sitemap_cache_hours", 24)), 1)
            urls = self._load_url_cache(store.slug, cache_hours)
            config["sitemap_cache_hit"] = urls is not None
            urls = urls or []
            visited: set[str] = set()
            sitemap_errors: list[str] = []
            cache_changed = False
            if not urls and sitemap_urls:
                for sitemap in sitemap_urls:
                    try:
                        urls.extend(await self._sitemap(client, str(sitemap), visited, 200_000))
                        cache_changed = True
                    except (httpx.HTTPError, ElementTree.ParseError, OSError, ValueError) as exc:
                        sitemap_errors.append(f"{sitemap}: {type(exc).__name__}: {exc}"[:500])
            patterns = [value.lower() for value in config.get("product_url_contains", [])]
            regexes = [
                re.compile(value, re.IGNORECASE) for value in config.get("product_url_regex", [])
            ]
            discovery_errors: list[str] = []
            if discovery_urls:
                discovered, discovery_errors = await self._discover_pages(
                    client,
                    store,
                    [str(url) for url in discovery_urls],
                    patterns,
                    regexes,
                    config,
                    robots,
                )
                if discovered:
                    urls.extend(discovered)
                    cache_changed = True
            if patterns or regexes:
                urls = [
                    url
                    for url in urls
                    if any(value in url.lower() for value in patterns)
                    or any(pattern.search(url) for pattern in regexes)
                ]
            urls = list(dict.fromkeys(urls))
            if not urls:
                details = "; ".join([*sitemap_errors, *discovery_errors]) or "product URL not found"
                raise RuntimeError(f"Sitemap {store.slug}: {details}")
            if cache_changed or not config["sitemap_cache_hit"]:
                self._save_url_cache(store.slug, urls)
            limit = min(
                int(config.get("max_pages_per_run", settings.collector_max_pages_per_run)),
                settings.collector_max_pages_per_run,
            )
            offset = int(config.get("crawl_offset", 0)) % len(urls)
            selected = (urls[offset:] + urls[:offset])[:limit]
            config["crawl_offset"] = (offset + len(selected)) % len(urls)
            config["discovered_urls"] = len(urls)
            config["sitemap_errors"] = sitemap_errors[-10:]
            config["discovery_errors"] = discovery_errors[-10:]
            items: list[OfferImportItem] = []
            page_errors = 0
            for index, url in enumerate(selected):
                if robots and not robots.can_fetch(settings.collector_user_agent, url):
                    continue
                try:
                    response = await _get_with_retry(client, url)
                    parsed = parse_jsonld_offer(response.text, url, store.slug)
                    harvested = extract_product(
                        response.text,
                        str(response.url),
                        store.slug,
                        config.get("selectors", {}),
                    )
                    if parsed is None:
                        if harvested and harvested.price is not None:
                            parsed = OfferImportItem.model_validate(harvested.model_dump())
                    elif harvested:
                        parsed.ean = parsed.ean or harvested.ean
                        parsed.mpn = parsed.mpn or harvested.mpn
                        parsed.brand = parsed.brand or harvested.brand
                        parsed.category = parsed.category or harvested.category
                        parsed.image_url = parsed.image_url or harvested.image_url
                        parsed.specs = {**harvested.specs, **parsed.specs}
                    if parsed:
                        parsed.source_metadata.update(
                            {
                                "enrichment": bool(config.get("enrichment_only")),
                                "sitemap_source": True,
                            }
                        )
                        items.append(parsed)
                except httpx.HTTPError:
                    page_errors += 1
                if index + 1 < len(selected):
                    await asyncio.sleep(settings.collector_min_delay_seconds)
            config["last_batch"] = {
                "selected": len(selected),
                "extracted": len(items),
                "errors": page_errors,
                "offset_start": offset,
                "offset_next": config["crawl_offset"],
            }
            store.parser_config = config
            return items

    async def _discover_pages(
        self,
        client: httpx.AsyncClient,
        store: Store,
        seeds: list[str],
        product_patterns: list[str],
        product_regexes: list[re.Pattern[str]],
        config: dict[str, Any],
        robots: RobotFileParser | None,
    ) -> tuple[list[str], list[str]]:
        """Rotate through public category pages and collect product links.

        This is used for shops that do not publish a product sitemap. Only a small,
        configurable page window is inspected per run; the URL cache accumulates the
        discovered products without blocking the UI for several minutes.
        """

        pages_per_run = min(max(int(config.get("discovery_pages_per_run", 8)), 1), 50)
        max_pages = min(max(int(config.get("discovery_max_pages_per_category", 40)), 1), 200)
        candidates = [
            self._with_page(seed, page) for page in range(1, max_pages + 1) for seed in seeds
        ]
        if not candidates:
            return [], []
        offset = int(config.get("discovery_offset", 0)) % len(candidates)
        selected = (candidates[offset:] + candidates[:offset])[:pages_per_run]
        config["discovery_offset"] = (offset + len(selected)) % len(candidates)
        discovered: list[str] = []
        errors: list[str] = []
        for index, page_url in enumerate(selected):
            if robots and not robots.can_fetch(settings.collector_user_agent, page_url):
                errors.append(f"{page_url}: blocked by robots.txt")
                continue
            try:
                response = await _get_with_retry(client, page_url)
                soup = BeautifulSoup(response.text, "html.parser")
                for anchor in soup.find_all("a", href=True):
                    link = urljoin(str(response.url), str(anchor["href"]))
                    if urlparse(link).netloc != urlparse(store.base_url).netloc:
                        continue
                    if any(value in link.lower() for value in product_patterns) or any(
                        pattern.search(link) for pattern in product_regexes
                    ):
                        discovered.append(link.split("#", 1)[0])
            except httpx.HTTPError as exc:
                errors.append(f"{page_url}: {type(exc).__name__}: {exc}"[:500])
            if index + 1 < len(selected):
                await asyncio.sleep(settings.collector_min_delay_seconds)
        config["last_discovery_batch"] = {
            "selected": len(selected),
            "found": len(discovered),
            "offset_start": offset,
            "offset_next": config["discovery_offset"],
        }
        return list(dict.fromkeys(discovered)), errors

    @staticmethod
    def _with_page(url: str, page: int) -> str:
        parsed = urlparse(url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        query["p"] = [str(page)]
        return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

    @staticmethod
    def _cache_path(slug: str) -> Path:
        safe_slug = re.sub(r"[^a-z0-9-]", "-", slug.lower())
        return CACHE_DIR / f"{safe_slug}-urls.json.gz"

    @classmethod
    def _load_url_cache(cls, slug: str, max_age_hours: int) -> list[str] | None:
        path = cls._cache_path(slug)
        try:
            if time.time() - path.stat().st_mtime > max_age_hours * 3600:
                return None
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                payload = json.load(handle)
            urls = payload.get("urls", [])
            return [str(url) for url in urls if str(url).startswith(("http://", "https://"))]
        except (OSError, ValueError, TypeError):
            return None

    @classmethod
    def _save_url_cache(cls, slug: str, urls: list[str]) -> None:
        path = cls._cache_path(slug)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            with gzip.open(temporary, "wt", encoding="utf-8") as handle:
                json.dump({"urls": urls}, handle, ensure_ascii=False)
            temporary.replace(path)
        except OSError:
            return

    @staticmethod
    async def _robots(client: httpx.AsyncClient, base_url: str) -> RobotFileParser | None:
        parsed = urlparse(base_url)
        try:
            response = await _get_with_retry(
                client, f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            )
        except httpx.HTTPError:
            return None
        robots = RobotFileParser()
        robots.parse(response.text.splitlines())
        return robots

    async def _sitemap(
        self,
        client: httpx.AsyncClient,
        url: str,
        visited: set[str],
        remaining: int,
    ) -> list[str]:
        if url in visited or remaining <= 0 or len(visited) >= 500:
            return []
        visited.add(url)
        response = await _get_with_retry(client, url)
        content = response.content
        if response.url.path.endswith(".gz"):
            content = gzip.decompress(content)
        root = ElementTree.fromstring(content)
        locations = [
            (node.text or "").strip()
            for node in root.findall(".//{*}loc")
            if (node.text or "").strip()
        ]
        if root.tag.split("}")[-1].lower() != "sitemapindex":
            return locations[:remaining]
        result: list[str] = []
        for child in locations:
            result.extend(await self._sitemap(client, child, visited, remaining - len(result)))
            if len(result) >= remaining:
                break
        return result[:remaining]
