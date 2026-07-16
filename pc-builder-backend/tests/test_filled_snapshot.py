import json
from decimal import Decimal
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SNAPSHOT = DATA_DIR / "starter-snapshot-pl-2026-07-15.json"
ROOT_DIR = DATA_DIR.parents[1]


def test_filled_snapshot_contains_only_ready_products_and_postgres_is_runtime() -> None:
    payload = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    items = payload["items"]

    assert len(items) >= 300
    assert len({item["external_id"] for item in items}) == len(items)
    assert {
        "cpu",
        "motherboard",
        "gpu",
        "ram",
        "storage",
        "psu",
        "case",
        "cooler",
        "monitor",
        "mouse",
        "keyboard",
        "headphones",
        "webcam",
    }.issubset({item["category"] for item in items})
    assert all(Decimal(item["price"]) > 0 for item in items)
    assert all(item["url"].startswith("https://www.x-kom.pl/p/") for item in items)
    assert all(item["image_url"].startswith("https://cdn.x-kom.pl/") for item in items)
    compose = (ROOT_DIR / "docker-compose.yml").read_text(encoding="utf-8")
    assert "postgres:15-alpine" in compose
    assert "postgresql+asyncpg://" in compose
    assert "CATALOG_AUTO_IMPORT" not in compose
