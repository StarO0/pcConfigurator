from io import BytesIO

from openpyxl import Workbook


def test_csv_and_xlsx_file_preview(client, admin_headers):
    csv_preview = client.post(
        "/api/v1/admin/file-preview",
        headers=admin_headers,
        files={
            "file": (
                "products.csv",
                "name;brand;category;sku;spec_socket\nRyzen 7 9700X;AMD;cpu;CSV-9700X;AM5\n",
                "text/csv",
            )
        },
    )
    assert csv_preview.status_code == 200, csv_preview.text
    assert csv_preview.json()["total"] == 1
    assert csv_preview.json()["rows"][0]["spec_socket"] == "AM5"

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["Name", "Brand", "Category", "SKU", "Price"])
    worksheet.append(["GeForce RTX 5070", "NVIDIA", "gpu", "XLSX-5070", 2999.9])
    payload = BytesIO()
    workbook.save(payload)
    xlsx_preview = client.post(
        "/api/v1/admin/file-preview",
        headers=admin_headers,
        files={
            "file": (
                "products.xlsx",
                payload.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert xlsx_preview.status_code == 200, xlsx_preview.text
    assert xlsx_preview.json()["rows"][0]["price"] == 2999.9


def test_product_import_normalization_full_catalog_and_duplicates(client, admin_headers):
    imported = client.post(
        "/api/v1/admin/product-tools/import",
        headers=admin_headers,
        json={
            "products": [
                {
                    "category": "cpu",
                    "brand": "AMD",
                    "name": "Ryzen 7 9700X Test Bulk",
                    "sku": "BULK-9700X-A",
                    "specs": {"Socket Type": "am5", "TDP": "65 W"},
                },
                {
                    "category": "cpu",
                    "brand": "AMD",
                    "name": "Ryzen 7 9700X Test Bulk",
                    "sku": "BULK-9700X-B",
                    "specs": {"socket": "AM5"},
                },
            ]
        },
    )
    assert imported.status_code == 200, imported.text
    assert imported.json()["created"] == 2

    full_catalog = client.get(
        "/api/v1/products",
        params={"search": "BULK-9700X-A", "in_stock": "false", "limit": 10},
    )
    assert full_catalog.status_code == 200, full_catalog.text
    product = full_catalog.json()["items"][0]
    assert product["offers"] == []
    assert product["specs"]["socket"] == "AM5"
    assert product["specs"]["power_w"] == 65
    assert product["specs"]["normalization_version"] == 2

    hidden_without_offer = client.get(
        "/api/v1/products",
        params={"search": "BULK-9700X-A", "in_stock": "true", "limit": 10},
    )
    assert hidden_without_offer.status_code == 200
    assert hidden_without_offer.json()["total"] == 0

    duplicate_groups = client.get(
        "/api/v1/admin/product-tools/duplicates?limit=200",
        headers=admin_headers,
    )
    assert duplicate_groups.status_code == 200, duplicate_groups.text
    assert any(len(group["products"]) >= 2 for group in duplicate_groups.json())


def test_normalization_backup_and_combined_price_history(client, admin_headers):
    dry_run = client.post(
        "/api/v1/admin/product-tools/normalize?dry_run=true",
        headers=admin_headers,
    )
    assert dry_run.status_code == 200, dry_run.text
    assert dry_run.json()["dry_run"] is True
    assert dry_run.json()["scanned"] > 0

    backup = client.get("/api/v1/admin/local-backup", headers=admin_headers)
    assert backup.status_code == 409, backup.text
    assert "PostgreSQL" in backup.json()["detail"]

    product = client.get(
        "/api/v1/products",
        params={"category": "gpu", "limit": 1},
    ).json()["items"][0]
    history = client.get(f"/api/v1/products/{product['id']}/price-history?days=365")
    assert history.status_code == 200, history.text
    assert history.json()["points"]
    assert all("store_name" in point for point in history.json()["points"])
