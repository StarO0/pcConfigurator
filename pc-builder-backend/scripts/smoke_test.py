from __future__ import annotations

import os
import time

import httpx

BASE_URL = os.getenv("SMOKE_BASE_URL", "http://127.0.0.1:8000/api/v1")


def expect(response, status: int, step: str):
    if response.status_code != status:
        raise AssertionError(
            f"{step}: ожидался HTTP {status}, получен {response.status_code}: {response.text}"
        )
    return response.json()


def run() -> None:
    email = f"smoke-{int(time.time())}-{os.getpid()}@example.com"
    password = "Smoke-password-123"
    with httpx.Client(base_url=BASE_URL, timeout=60) as client:
        health = expect(client.get("/api/v1/health"), 200, "health")
        assert health["status"] == "ok"

        catalog = expect(client.get("/api/v1/catalog/status"), 200, "catalog status")
        assert catalog["products"] >= 300, catalog
        catalog_page = expect(
            client.get("/api/v1/products?in_stock=false&limit=1"),
            200,
            "full catalog page",
        )
        assert catalog_page["total"] >= 300
        priced_page = expect(
            client.get("/api/v1/products?in_stock=true&limit=20&sort=price"),
            200,
            "starter offers",
        )
        assert priced_page["total"] >= 300, priced_page
        assert all(row["image_url"] for row in priced_page["items"]), priced_page
        assert all(row["offers"] for row in priced_page["items"]), priced_page
        assert any(
            offer.get("source_metadata", {}).get("snapshot")
            for row in priced_page["items"]
            for offer in row["offers"]
        ), priced_page

        admin_tokens = expect(
            client.post(
                "/api/v1/auth/login",
                json={"email": "admin@pcbuilder.app", "password": "Local-admin-123"},
            ),
            200,
            "admin login",
        )
        admin_auth = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
        dashboard = expect(
            client.get("/api/v1/admin/harvester/dashboard", headers=admin_auth),
            200,
            "harvester dashboard",
        )
        assert dashboard["accepted"] >= 330, dashboard
        assert dashboard["snapshot_offers"] >= 330, dashboard
        enrichment = expect(
            client.get("/api/v1/admin/harvester/enrichment/status", headers=admin_auth),
            200,
            "catalog acquisition status",
        )
        assert enrichment["products"] >= 300, enrichment
        assert enrichment["products_with_offers"] >= 300, enrichment
        assert enrichment["products_complete"] >= 300, enrichment
        assert {store["slug"] for store in enrichment["stores"]} >= {
            "x-kom",
            "morele",
            "komputronik",
            "rtv-euro-agd",
        }
        rejected_run = client.post(
            f"/api/v1/admin/harvester/enrichment/run/{enrichment['stores'][0]['id']}",
            headers=admin_auth,
            json={"pages": 10, "terms_confirmed": False},
        )
        assert rejected_run.status_code == 409, rejected_run.text

        tokens = expect(
            client.post(
                "/api/v1/auth/register",
                json={"email": email, "display_name": "Smoke Test", "password": password},
            ),
            201,
            "register",
        )
        auth = {"Authorization": f"Bearer {tokens['access_token']}"}

        generated = expect(
            client.post(
                "/api/v1/builds/generate",
                json={
                    "prompt": "Игровой компьютер до 6000 PLN для 1440p",
                    "language": "ru",
                    "basket_mode": "balanced",
                },
                headers=auth,
            ),
            200,
            "generate",
        )
        assert len(generated["builds"]) >= 1
        build = generated["builds"][0]
        build_id = build["id"]
        guest = {"X-Build-Token": build["access_token"]}

        manual = expect(
            client.post(
                "/api/v1/builds/manual",
                headers=auth,
                json={
                    "name": "Smoke manual build",
                    "components": {
                        row["category"]: row["product"]["id"] for row in build["components"]
                    },
                    "language": "ru",
                },
            ),
            201,
            "manual build",
        )
        assert manual["is_saved"] is True

        analysis = expect(
            client.get(f"/api/v1/builds/{build_id}/analysis?language=ru", headers=guest),
            200,
            "analysis",
        )
        assert analysis["build_id"] == build_id

        options = expect(
            client.get(
                f"/api/v1/builds/{build_id}/replacement-options/cpu?limit=40", headers=guest
            ),
            200,
            "replacement options",
        )
        current_cpu = next(
            row["product"]["id"] for row in build["components"] if row["category"] == "cpu"
        )
        replacement = next(row for row in options if row["product"]["id"] != current_cpu)
        changed = expect(
            client.patch(
                f"/api/v1/builds/{build_id}/components/cpu",
                headers=guest,
                json={
                    "product_id": replacement["product"]["id"],
                    "expected_version": build["version"],
                    "basket_mode": "balanced",
                },
            ),
            200,
            "replace component",
        )
        assert changed["version"] > build["version"]

        saved = expect(
            client.post(f"/api/v1/builds/{build_id}/save", headers={**auth, **guest}),
            200,
            "save",
        )
        assert saved["is_saved"] is True

        saved_list = expect(
            client.get("/api/v1/builds/saved/me/list", headers=auth), 200, "saved list"
        )
        assert any(row["id"] == build_id for row in saved_list)

        owner_options = expect(
            client.get(f"/api/v1/builds/{build_id}/replacement-options/gpu?limit=40", headers=auth),
            200,
            "owner replacement options",
        )
        assert owner_options

        expect(client.delete(f"/api/v1/builds/{build_id}", headers=auth), 200, "delete build")
        expect(client.delete("/api/v1/auth/me", headers=auth), 200, "delete account")

    print(
        "SMOKE OK: PostgreSQL, 300+ готовых товаров с ценами и фото, "
        "Open Icecat acquisition, harvester, API, регистрация, "
        "AI/ручная сборка, анализ, замена, сохранение и удаление"
    )


if __name__ == "__main__":
    run()
