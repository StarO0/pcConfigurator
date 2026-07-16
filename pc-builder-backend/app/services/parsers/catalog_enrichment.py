from __future__ import annotations

from app.models.entities import Store
from app.schemas.products import OfferImportItem
from app.services.catalog.open_icecat import enrich_offer_items
from app.services.parsers.jsonld_sitemap import JsonLdSitemapParser


class CatalogAcquisitionParser(JsonLdSitemapParser):
    """Build ready product cards from Polish offers and Open Icecat data."""

    async def fetch(self, store: Store) -> list[OfferImportItem]:
        config = dict(store.parser_config or {})
        config["enrichment_only"] = False
        config["create_unmatched_products"] = True
        config["require_complete_card"] = True
        store.parser_config = config
        items = await super().fetch(store)
        items, enriched = await enrich_offer_items(items)
        config = dict(store.parser_config or {})
        config["last_icecat_enriched"] = enriched
        config["last_ready_candidates"] = len(items)
        store.parser_config = config
        return items


class CatalogEnrichmentParser(CatalogAcquisitionParser):
    """Backward-compatible name for databases created by versions 5.x."""
