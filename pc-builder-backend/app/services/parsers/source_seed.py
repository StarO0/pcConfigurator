from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.entities import Store

SOURCE_STORES = [
    {
        "slug": "ceneo",
        "name": "Ceneo",
        "base_url": "https://www.ceneo.pl",
        "parser_type": "ceneo",
        "parser_config": {"create_unmatched_products": True, "aggregate": True},
    },
    {
        "slug": "x-kom",
        "name": "x-kom",
        "base_url": "https://www.x-kom.pl",
        "parser_type": "catalog_acquisition",
        "parser_config": {
            "sitemap_urls": ["https://www.x-kom.pl/sitemap.xml"],
            "product_url_contains": ["/p/"],
            "create_unmatched_products": True,
            "require_complete_card": True,
            "max_pages_per_run": 25,
            "schedule_minutes": 360,
            "terms_confirmed": False,
        },
    },
    {
        "slug": "morele",
        "name": "Morele",
        "base_url": "https://www.morele.net",
        "parser_type": "catalog_acquisition",
        "parser_config": {
            "sitemap_urls": [
                "https://www.morele.net/product_active_sitemap_13_podzespoly_komputerowe.xml",
                "https://www.morele.net/product_active_sitemap_255_chlodzenie_komputerowe.xml",
                "https://www.morele.net/product_active_sitemap_27_dyski_i_nosniki_danych.xml",
                "https://www.morele.net/product_active_sitemap_34_monitory.xml",
                "https://www.morele.net/product_active_sitemap_15_klawiatury_i_myszki.xml",
                "https://www.morele.net/product_active_sitemap_56_sprzet_dla_graczy.xml",
                "https://www.morele.net/product_active_sitemap_114_sluchawki_i_mikrofony.xml",
                "https://www.morele.net/product_active_sitemap_940_glosniki_mikrofony_kamerki.xml",
                "https://www.morele.net/product_active_sitemap_16_urzadzenia_sieciowe.xml",
                "https://www.morele.net/product_active_sitemap_119_kable_i_adaptery.xml",
                "https://www.morele.net/product_active_sitemap_90_zasilanie.xml",
            ],
            "product_url_regex": [r"-\d+/$"],
            "create_unmatched_products": True,
            "require_complete_card": True,
            "max_pages_per_run": 25,
            "schedule_minutes": 360,
            "terms_confirmed": False,
        },
    },
    {
        "slug": "komputronik",
        "name": "Komputronik",
        "base_url": "https://www.komputronik.pl",
        "parser_type": "catalog_acquisition",
        "parser_config": {
            "sitemap_urls": [],
            "discovery_urls": [
                "https://www.komputronik.pl/category/401/procesory.html",
                "https://www.komputronik.pl/category/1099/karty-graficzne.html",
                "https://www.komputronik.pl/category/437/pamiec-ram.html",
                "https://www.komputronik.pl/category/757/plyty-glowne.html",
                "https://www.komputronik.pl/category/857/dyski.html",
                "https://www.komputronik.pl/category/2701/obudowy-komputerowe.html",
                "https://www.komputronik.pl/category/2869/zasilacze-komputerowe.html",
                "https://www.komputronik.pl/category/3215/chlodzenie.html",
                "https://www.komputronik.pl/category/1251/monitory.html",
                "https://www.komputronik.pl/category/6569/klawiatury-pc.html",
                "https://www.komputronik.pl/category/2954/myszki-komputerowe.html",
                "https://www.komputronik.pl/category/8077/sluchawki.html",
                "https://www.komputronik.pl/category/3033/glosniki.html",
                "https://www.komputronik.pl/category/8083/mikrofony.html",
                "https://www.komputronik.pl/category/1754/kamery-internetowe.html",
                "https://www.komputronik.pl/category/2998/kontrolery-do-gier-pc.html",
                "https://www.komputronik.pl/category/2372/karty-sieciowe.html",
                "https://www.komputronik.pl/category/1054/napedy-optyczne.html",
                "https://www.komputronik.pl/category/1212/karty-dzwiekowe.html",
                "https://www.komputronik.pl/category/8874/dyski-zewnetrzne.html",
            ],
            "product_url_contains": ["/product/"],
            "discovery_pages_per_run": 8,
            "discovery_max_pages_per_category": 40,
            "create_unmatched_products": True,
            "require_complete_card": True,
            "max_pages_per_run": 25,
            "schedule_minutes": 360,
            "terms_confirmed": False,
        },
    },
    {
        "slug": "rtv-euro-agd",
        "name": "RTV EURO AGD",
        "base_url": "https://www.euro.com.pl",
        "parser_type": "catalog_acquisition",
        "parser_config": {
            "sitemap_urls": [
                "https://www.euro.com.pl/sitemap-produkty-komputery.xml",
                "https://www.euro.com.pl/sitemap-produkty-gry-i-konsole.xml",
                "https://www.euro.com.pl/sitemap-produkty-rtv.xml",
            ],
            "product_url_contains": [".bhtml"],
            "create_unmatched_products": True,
            "require_complete_card": True,
            "max_pages_per_run": 25,
            "schedule_minutes": 360,
            "terms_confirmed": False,
        },
    },
    {
        "slug": "media-expert",
        "name": "Media Expert",
        "base_url": "https://www.mediaexpert.pl",
        "parser_type": "manual",
        "parser_config": {
            "mode": "official_feed_required",
            "supported_feed_types": ["csv", "json", "xml"],
        },
    },
]

SOURCE_TOPOLOGY_KEYS = {
    "sitemap_urls",
    "product_url_contains",
    "product_url_regex",
    "discovery_urls",
    "discovery_pages_per_run",
    "discovery_max_pages_per_category",
}


async def seed_source_stores(session: AsyncSession) -> None:
    existing = {item.slug: item for item in (await session.execute(select(Store))).scalars()}
    for data in SOURCE_STORES:
        current = existing.get(data["slug"])
        if current is not None:
            if data["parser_type"] == "catalog_acquisition":
                previous = dict(current.parser_config or {})
                current.parser_type = "catalog_acquisition"
                merged = {
                    **data["parser_config"],
                    **previous,
                    "create_unmatched_products": True,
                    "require_complete_card": True,
                    "enrichment_only": False,
                    "terms_confirmed": bool(previous.get("terms_confirmed", False)),
                }
                for key in SOURCE_TOPOLOGY_KEYS:
                    if key in data["parser_config"]:
                        merged[key] = data["parser_config"][key]
                    else:
                        merged.pop(key, None)
                current.parser_config = merged
            continue
        is_ceneo = data["slug"] == "ceneo"
        enabled = (
            settings.ceneo_enabled and bool(settings.ceneo_api_key_value)
            if is_ceneo
            else settings.public_collectors_enabled and data["parser_type"] != "manual"
        )
        session.add(Store(**data, is_active=enabled))
    await session.commit()
