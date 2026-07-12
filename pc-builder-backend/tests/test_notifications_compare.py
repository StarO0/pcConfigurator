import asyncio

from app.workers.tasks import _check_price_alerts


def test_price_alert_worker_and_notifications(client, auth_headers):
    product = client.get(
        "/api/v1/products",
        params={"category": "gpu", "limit": 1},
    ).json()["items"][0]
    current_price = min(
        float(item["effective_price"]) for item in product["offers"] if item["in_stock"]
    )
    created = client.post(
        "/api/v1/price-alerts",
        headers=auth_headers,
        json={
            "product_id": product["id"],
            "target_price": current_price + 1,
            "currency": "PLN",
        },
    )
    assert created.status_code == 200, created.text

    result = asyncio.run(_check_price_alerts())
    assert result["sent"] >= 1

    notifications = client.get("/api/v1/notifications", headers=auth_headers)
    assert notifications.status_code == 200
    item = next(
        notification
        for notification in notifications.json()["items"]
        if notification["data"].get("product_id") == product["id"]
    )
    read = client.post(
        f"/api/v1/notifications/{item['id']}/read",
        headers=auth_headers,
    )
    assert read.status_code == 200
    assert read.json()["read_at"] is not None


def test_compare_and_export_private_builds(client):
    generated = client.post(
        "/api/v1/builds/generate",
        json={"prompt": "Игровой компьютер до 6000 PLN для 1440p"},
    )
    assert generated.status_code == 200, generated.text
    left, right = generated.json()["builds"][:2]

    compared = client.post(
        "/api/v1/builds/compare",
        json={
            "left_id": left["id"],
            "right_id": right["id"],
            "left_token": left["access_token"],
            "right_token": right["access_token"],
        },
    )
    assert compared.status_code == 200, compared.text
    assert len(compared.json()["differences"]) == 8

    exported = client.get(
        f"/api/v1/builds/{left['id']}/export",
        headers={"X-Build-Token": left["access_token"]},
    )
    assert exported.status_code == 200, exported.text
    assert exported.headers["content-disposition"].endswith('.json"')
    assert exported.json()["id"] == left["id"]
