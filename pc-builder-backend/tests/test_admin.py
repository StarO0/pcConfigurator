def test_admin_product_store_service_token_and_import(client, admin_headers):
    stats = client.get("/api/v1/admin/stats", headers=admin_headers)
    assert stats.status_code == 200
    assert stats.json()["products"] >= 20

    token_response = client.post(
        "/api/v1/admin/service-tokens",
        headers=admin_headers,
        json={"name": "test-importer", "scopes": ["offers:write"]},
    )
    assert token_response.status_code == 201, token_response.text
    service_token = token_response.json()["token"]

    imported = client.post(
        "/api/v1/admin/offers/import",
        headers={"X-Service-Token": service_token},
        json={
            "offers": [
                {
                    "product_sku": "GPU-RTX4060",
                    "mpn": "GPU-RTX4060",
                    "title": "GeForce RTX 4060 8GB",
                    "store_slug": "demotech",
                    "external_id": "external-new-4060",
                    "url": "https://example.com/demotech/new-4060",
                    "price": "1199.00",
                    "shipping_price": "0",
                    "currency": "PLN",
                    "in_stock": True,
                    "stock_quantity": 5,
                }
            ]
        },
    )
    assert imported.status_code == 200, imported.text
    assert imported.json()["created"] == 1

    product_created = client.post(
        "/api/v1/admin/products",
        headers=admin_headers,
        json={
            "category": "storage",
            "brand": "Test",
            "name": "Test NVMe 4TB",
            "sku": "TEST-NVME-4T",
            "performance_score": 75,
            "specs": {
                "interface": "NVMe",
                "capacity_gb": 4000,
                "form_factor": 2280,
                "pcie_generation": 4,
            },
        },
    )
    assert product_created.status_code == 201, product_created.text


def test_admin_xml_preview(client, admin_headers):
    payload = b"""<?xml version="1.0" encoding="UTF-8"?>
    <catalog>
      <product sku="XML-CPU-1">
        <category>cpu</category>
        <brand>Example</brand>
        <name>Example CPU</name>
        <specs><socket>AM5</socket><cores>8</cores></specs>
      </product>
      <product sku="XML-GPU-1">
        <category>gpu</category>
        <brand>Example</brand>
        <name>Example GPU</name>
      </product>
    </catalog>
    """
    response = client.post(
        "/api/v1/admin/file-preview",
        headers=admin_headers,
        files={"file": ("catalog.xml", payload, "application/xml")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 2
    assert body["rows"][0]["sku"] == "XML-CPU-1"
    assert body["rows"][0]["specs_socket"] == "AM5"


def test_admin_xml_preview_rejects_doctype(client, admin_headers):
    response = client.post(
        "/api/v1/admin/file-preview",
        headers=admin_headers,
        files={
            "file": (
                "unsafe.xml",
                b'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
                "application/xml",
            )
        },
    )
    assert response.status_code == 422
