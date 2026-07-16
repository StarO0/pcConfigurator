import httpx
import pytest

from app.models.entities import Store
from app.services.catalog.open_icecat import OpenIcecatClient
from app.services.harvester.extraction import decimal_price, extract_product
from app.services.parsers.jsonld_sitemap import JsonLdSitemapParser, parse_jsonld_offer
from app.services.parsers.source_seed import SOURCE_STORES


def test_catalog_status_and_categories(client):
    status = client.get("/api/v1/catalog/status")
    assert status.status_code == 200, status.text
    payload = status.json()
    assert payload["products"] >= 8
    assert payload["active_offers"] > 0
    assert {source["slug"] for source in payload["sources"]} >= {
        "ceneo",
        "x-kom",
        "morele",
        "komputronik",
        "rtv-euro-agd",
        "media-expert",
    }
    categories = client.get("/api/v1/catalog/categories")
    assert categories.status_code == 200
    assert {item["category"] for item in categories.json()} >= {"cpu", "gpu", "motherboard"}


def test_jsonld_product_parser():
    html = """
    <html><head><script type="application/ld+json">
    {
      "@type": "Product",
      "name": "AMD Ryzen 7 9700X",
      "sku": "10001",
      "gtin13": "1234567890123",
      "brand": {"@type": "Brand", "name": "AMD"},
      "category": "Procesory",
      "image": "https://example.com/cpu.jpg",
      "offers": {
        "@type": "Offer",
        "price": "1499,00",
        "priceCurrency": "PLN",
        "availability": "https://schema.org/InStock",
        "url": "https://example.com/ryzen"
      }
    }
    </script></head></html>
    """
    offer = parse_jsonld_offer(html, "https://example.com/p/10001", "example")
    assert offer is not None
    assert offer.title == "AMD Ryzen 7 9700X"
    assert offer.category == "cpu"
    assert str(offer.price) == "1499.00"
    assert offer.in_stock is True
    assert offer.ean == "1234567890123"


def test_jsonld_full_schema_type_relative_urls_and_price_locales():
    html = """
    <script type="application/ld+json">
    {"@type":"https://schema.org/Product","name":"Acme 2TB SSD",
     "brand":{"name":"Acme"},"image":"/media/ssd.jpg",
     "offers":{"@type":"https://schema.org/Offer","price":"1,299.00",
     "priceCurrency":"PLN","url":"/product/ssd"}}
    </script>
    """
    item = extract_product(html, "https://shop.example/catalog/ssd", "shop-example")
    assert item is not None
    assert str(item.price) == "1299.00"
    assert str(item.image_url) == "https://shop.example/media/ssd.jpg"
    assert str(item.url) == "https://shop.example/product/ssd"
    assert str(decimal_price("1.299,00 zł")) == "1299.00"


def test_jsonld_object_category_used_by_angular_storefronts():
    html = """
    <script type="application/ld+json">
    {"@type":"Product","name":"TP-Link Network Adapter","image":"/adapter.webp",
     "category":{"@type":"Thing","name":"Karty sieciowe"},
     "offers":{"@type":"Offer","price":"149,99","priceCurrency":"PLN"}}
    </script>
    """
    item = parse_jsonld_offer(html, "https://shop.example/adapter.bhtml", "shop-example")
    assert item is not None
    assert item.category == "network"
    assert str(item.price) == "149.99"


def test_curated_enrichment_sources_use_real_discovery_topology():
    sources = {item["slug"]: item for item in SOURCE_STORES}
    morele = sources["morele"]["parser_config"]
    assert any("product_active_sitemap_13_" in url for url in morele["sitemap_urls"])
    assert morele["product_url_regex"] == [r"-\d+/$"]
    euro = sources["rtv-euro-agd"]["parser_config"]
    assert "https://www.euro.com.pl/sitemap-produkty-komputery.xml" in euro["sitemap_urls"]
    komputronik = sources["komputronik"]["parser_config"]
    assert komputronik["sitemap_urls"] == []
    assert len(komputronik["discovery_urls"]) >= 15
    assert all(
        source["parser_config"].get("create_unmatched_products", False)
        and source["parser_config"].get("require_complete_card", False)
        for source in sources.values()
        if source["parser_type"] == "catalog_acquisition"
    )


@pytest.mark.asyncio
async def test_open_icecat_keyless_lookup_parses_identity_images_and_specs():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["shopname"] == "openIcecat-live"
        assert request.url.params["GTIN"] == "4948570114344"
        return httpx.Response(
            200,
            request=request,
            json={
                "data": {
                    "GeneralInfo": {
                        "IcecatId": 29900045,
                        "Title": "iiyama ProLite X4071UHSU-B1 monitor",
                        "Brand": "iiyama",
                        "BrandPartCode": "X4071UHSU-B1",
                        "GTIN": ["4948570114344"],
                        "Category": {"Name": {"Value": "Computer Monitors"}},
                        "Description": {"URL": "https://iiyama.example/product"},
                        "SummaryDescription": {"ShortSummaryDescription": "39.5 inch 4K display"},
                    },
                    "Image": {"HighPic": "https://images.icecat.biz/main.jpg"},
                    "Gallery": [
                        {"Pic": "https://images.icecat.biz/main.jpg"},
                        {"Pic": "https://images.icecat.biz/side.jpg"},
                    ],
                    "FeaturesGroups": [
                        {
                            "FeatureGroup": {"Name": {"Value": "Display"}},
                            "Features": [
                                {
                                    "PresentationValue": "3840 x 2160 pixels",
                                    "Feature": {"Name": {"Value": "Display resolution"}},
                                }
                            ],
                        }
                    ],
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        product = await OpenIcecatClient(http).lookup(gtin="4948 5701 14344")
    assert product is not None
    assert product.icecat_id == "29900045"
    assert product.image_url.endswith("main.jpg")
    assert product.gallery_urls[-1].endswith("side.jpg")
    assert product.features["Display resolution"] == "3840 x 2160 pixels"


@pytest.mark.asyncio
async def test_html_category_discovery_rotates_pages_and_resolves_product_links():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["p"] == "1"
        return httpx.Response(
            200,
            request=request,
            text='<a href="/product/42/example-gpu.html#details">GPU</a>',
        )

    store = Store(
        name="Example",
        slug="example",
        base_url="https://shop.example",
        parser_type="catalog_enrichment",
        parser_config={},
    )
    config = {"discovery_pages_per_run": 1, "discovery_max_pages_per_category": 3}
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        links, errors = await JsonLdSitemapParser()._discover_pages(
            client,
            store,
            ["https://shop.example/category/gpu.html"],
            ["/product/"],
            [],
            config,
            None,
        )
    assert errors == []
    assert links == ["https://shop.example/product/42/example-gpu.html"]
    assert config["discovery_offset"] == 1
