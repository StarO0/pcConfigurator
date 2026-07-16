from app.schemas.harvester import HarvestItem
from app.services.harvester.extraction import extract_product, parse_xml_feed
from app.services.harvester.ingest import complete_card_errors


def test_jsonld_and_selector_extraction_without_api() -> None:
    html = """
    <html><head>
      <meta property="og:image" content="https://img.example/board.jpg">
      <script type="application/ld+json">
      {"@context":"https://schema.org","@type":"Product","name":"Acme B650 Board",
       "brand":{"@type":"Brand","name":"Acme"},"sku":"AC-B650",
       "additionalProperty":[{"@type":"PropertyValue","name":"Socket","value":"AM5"}]}
      </script>
    </head><body><span class="price">629,99 zł</span></body></html>
    """
    product_only = extract_product(html, "https://shop.example/p/acme", "shop-example")
    assert product_only is not None
    assert product_only.price is None
    assert product_only.specs["Socket"] == "AM5"
    selected = extract_product(
        html,
        "https://shop.example/p/acme",
        "shop-example",
        {"price": ".price"},
    )
    assert selected is not None
    assert str(selected.price) == "629.99"
    assert str(selected.image_url) == "https://img.example/board.jpg"


def test_xml_yml_feed_extraction() -> None:
    items = parse_xml_feed(
        """
        <shop><offers><offer id="xml-1">
          <name>Acme DDR5 32GB</name><url>https://feed.example/acme-ddr5</url>
          <price>399.90</price><currencyId>PLN</currencyId><vendor>Acme</vendor>
          <category>RAM DDR5</category><picture>https://img.example/ram.jpg</picture>
        </offer></offers></shop>
        """,
        "xml-example",
    )
    assert len(items) == 1
    assert items[0].external_id == "xml-1"
    assert str(items[0].price) == "399.90"
    assert items[0].category == "ram"


def test_catalog_quality_gate_requires_a_complete_real_card() -> None:
    ready = HarvestItem(
        ean="4948570114344",
        title="iiyama ProLite X4071UHSU-B1",
        store_slug="polish-shop",
        external_id="offer-1",
        url="https://shop.example/product",
        price="1499.00",
        brand="iiyama",
        category="monitor",
        image_url="https://images.icecat.biz/main.jpg",
    )
    assert complete_card_errors(ready) == []
    incomplete = ready.model_copy(update={"image_url": None, "ean": None})
    assert complete_card_errors(incomplete) == ["https_image", "gtin_or_brand_mpn"]


def test_browser_import_staging_deduplication_and_dashboard(client, admin_headers) -> None:
    payload = {
        "source_slug": "collector-test",
        "source_name": "Collector Test",
        "source_base_url": "https://collector.example",
        "create_products": True,
        "auto_accept": True,
        "items": [
            {
                "product_sku": "COLLECTOR-GPU-1",
                "title": "Collector Radeon Test 16GB",
                "store_slug": "collector-test",
                "external_id": "gpu-1",
                "url": "https://collector.example/gpu-1",
                "price": "1999.00",
                "currency": "PLN",
                "in_stock": True,
                "brand": "Collector",
                "category": "gpu",
                "image_url": "https://collector.example/gpu-1.jpg",
                "specs": {"vram_gb": 16},
            }
        ],
    }
    imported = client.post(
        "/api/v1/admin/harvester/browser-import", headers=admin_headers, json=payload
    )
    assert imported.status_code == 200, imported.text
    assert imported.json()["accepted"] == 1
    assert imported.json()["products_created"] == 1
    assert imported.json()["offers_created"] == 1

    repeated = client.post(
        "/api/v1/admin/harvester/browser-import", headers=admin_headers, json=payload
    )
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["products_created"] == 0
    assert repeated.json()["offers_created"] == 0
    assert repeated.json()["duplicates"] >= 1

    catalog = client.get(
        "/api/v1/products",
        params={"search": "Collector Radeon Test", "in_stock": "true"},
    )
    assert catalog.status_code == 200, catalog.text
    product = catalog.json()["items"][0]
    assert product["image_url"].endswith("gpu-1.jpg")
    assert str(product["offers"][0]["price"]) == "1999.00"

    dashboard = client.get("/api/v1/admin/harvester/dashboard", headers=admin_headers)
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["accepted"] >= 1
    assert dashboard.json()["active_offers"] >= 1


def test_html_preview_and_manual_staging_approval(client, admin_headers) -> None:
    html = """
    <html><head><meta property="og:title" content="Manual Test Webcam">
    <meta property="og:image" content="https://manual.example/cam.jpg"></head>
    <body><h1>Manual Test Webcam</h1><div class="cost">129,00 PLN</div></body></html>
    """
    preview = client.post(
        "/api/v1/admin/harvester/extract-preview",
        headers=admin_headers,
        json={
            "html": html,
            "url": "https://manual.example/camera",
            "store_slug": "manual-staging",
            "selectors": {"price": ".cost"},
        },
    )
    assert preview.status_code == 200, preview.text
    item = preview.json()
    assert item["title"] == "Manual Test Webcam"
    assert str(item["price"]) == "129.00"

    staged = client.post(
        "/api/v1/admin/harvester/browser-import",
        headers=admin_headers,
        json={
            "source_slug": "manual-staging",
            "source_name": "Manual Staging",
            "source_base_url": "https://manual.example",
            "create_products": True,
            "auto_accept": False,
            "items": [item],
        },
    )
    assert staged.status_code == 200, staged.text
    assert staged.json()["pending"] == 1
    rows = client.get(
        "/api/v1/admin/harvester/records?status=pending",
        headers=admin_headers,
    )
    record = next(
        entry for entry in rows.json()["items"] if entry["store_slug"] == "manual-staging"
    )
    approved = client.post(
        f"/api/v1/admin/harvester/records/{record['id']}/approve",
        headers=admin_headers,
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["accepted"] == 1


def test_fuzzy_matching_never_crosses_product_categories(client, admin_headers) -> None:
    existing = client.post(
        "/api/v1/admin/products",
        headers=admin_headers,
        json={
            "category": "cooler",
            "brand": "Collision",
            "name": "Collision GAMING 360",
            "sku": "COLLISION-COOLER-360",
            "specs": {"radiator_mm": 360},
        },
    )
    assert existing.status_code == 201, existing.text

    imported = client.post(
        "/api/v1/admin/harvester/browser-import",
        headers=admin_headers,
        json={
            "source_slug": "collision-source",
            "source_name": "Collision Source",
            "source_base_url": "https://collision.example",
            "create_products": True,
            "auto_accept": True,
            "items": [
                {
                    "product_sku": "COLLISION-GPU-360",
                    "title": "Collision Radeon GAMING 360",
                    "store_slug": "collision-source",
                    "external_id": "gpu-360",
                    "url": "https://collision.example/gpu-360",
                    "price": "1299.00",
                    "brand": "Collision",
                    "category": "gpu",
                    "image_url": "https://collision.example/gpu-360.jpg",
                    "specs": {"vram_gb": 8},
                }
            ],
        },
    )
    assert imported.status_code == 200, imported.text
    assert imported.json()["products_created"] == 1

    catalog = client.get(
        "/api/v1/products",
        params={"search": "Collision Radeon", "in_stock": "true"},
    )
    assert catalog.status_code == 200, catalog.text
    assert catalog.json()["items"][0]["category"] == "gpu"


def test_fuzzy_subset_does_not_merge_different_models(client, admin_headers) -> None:
    existing = client.post(
        "/api/v1/admin/products",
        headers=admin_headers,
        json={
            "category": "gpu",
            "brand": "Subset",
            "name": "Subset Gaming OC",
            "sku": "SUBSET-GPU-GENERIC",
            "specs": {"vram_gb": 4},
        },
    )
    assert existing.status_code == 201, existing.text

    imported = client.post(
        "/api/v1/admin/harvester/browser-import",
        headers=admin_headers,
        json={
            "source_slug": "subset-source",
            "source_name": "Subset Source",
            "source_base_url": "https://subset.example",
            "items": [
                {
                    "product_sku": "SUBSET-RX7600",
                    "title": "Subset Radeon RX 7600 Gaming OC 8GB",
                    "store_slug": "subset-source",
                    "external_id": "rx7600",
                    "url": "https://subset.example/rx7600",
                    "price": "1199.00",
                    "brand": "Subset",
                    "category": "gpu",
                    "image_url": "https://subset.example/rx7600.jpg",
                    "specs": {"gpu_chip": "Radeon RX 7600", "vram_gb": 8},
                }
            ],
        },
    )
    assert imported.status_code == 200, imported.text
    assert imported.json()["products_created"] == 1


def test_variant_matching_uses_specs_and_never_guesses_ambiguous_rows(
    client, admin_headers
) -> None:
    for sku, speed, latency in (("VARIANT-3200", 3200, 16), ("VARIANT-3600", 3600, 18)):
        created = client.post(
            "/api/v1/admin/products",
            headers=admin_headers,
            json={
                "category": "ram",
                "brand": "VariantSafe",
                "name": "VariantSafe Memory 16 GB",
                "sku": sku,
                "specs": {
                    "capacity_gb": 16,
                    "ram_type": "DDR4",
                    "speed_mhz": speed,
                    "module_count": 2,
                    "cas_latency": latency,
                },
            },
        )
        assert created.status_code == 201, created.text

    payload = {
        "source_slug": "variant-safe-source",
        "source_name": "Variant Safe Source",
        "source_base_url": "https://variants.example",
        "create_products": False,
        "auto_accept": True,
        "items": [
            {
                "title": "VariantSafe Memory 16 GB",
                "store_slug": "variant-safe-source",
                "external_id": "variant-3600",
                "url": "https://variants.example/variant-3600",
                "price": "299.00",
                "brand": "VariantSafe",
                "category": "ram",
                "image_url": "https://variants.example/variant-3600.jpg",
                "specs": {
                    "capacity_gb": 16,
                    "ram_type": "DDR4",
                    "speed_mhz": 3600,
                    "module_count": 2,
                    "cas_latency": 18,
                },
            }
        ],
    }
    matched = client.post(
        "/api/v1/admin/harvester/browser-import",
        headers=admin_headers,
        json=payload,
    )
    assert matched.status_code == 200, matched.text
    assert matched.json()["accepted"] == 1
    assert matched.json()["offers_created"] == 1
    assert matched.json()["products_created"] == 0

    payload["items"][0].update(
        {
            "external_id": "ambiguous-variant",
            "url": "https://variants.example/ambiguous",
            "specs": {},
        }
    )
    ambiguous = client.post(
        "/api/v1/admin/harvester/browser-import",
        headers=admin_headers,
        json=payload,
    )
    assert ambiguous.status_code == 200, ambiguous.text
    assert ambiguous.json()["pending"] == 1
    assert ambiguous.json()["offers_created"] == 0
    pending = client.get("/api/v1/admin/harvester/records?status=pending", headers=admin_headers)
    ambiguous_record = next(
        row for row in pending.json()["items"] if row["external_id"] == "ambiguous-variant"
    )
    unsafe_approval = client.post(
        f"/api/v1/admin/harvester/records/{ambiguous_record['id']}/approve",
        headers=admin_headers,
    )
    assert unsafe_approval.status_code == 409

    status = client.get("/api/v1/admin/harvester/enrichment/status", headers=admin_headers)
    assert status.status_code == 200, status.text
    assert status.json()["pending_ambiguous"] >= 1
    assert {store["slug"] for store in status.json()["stores"]} >= {
        "x-kom",
        "morele",
        "komputronik",
        "rtv-euro-agd",
    }
