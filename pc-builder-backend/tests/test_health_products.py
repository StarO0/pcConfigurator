def test_health_and_catalog(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"

    products = client.get(
        "/api/v1/products",
        params={"category": "gpu", "sort": "performance", "limit": 10},
    )
    assert products.status_code == 200, products.text
    data = products.json()
    assert data["total"] >= 4
    assert all(item["category"] == "gpu" for item in data["items"])
    assert all(item["offers"] for item in data["items"])
    assert data["items"][0]["performance_score"] >= data["items"][-1]["performance_score"]


def test_favorites_and_price_history(client, auth_headers):
    product = client.get("/api/v1/products", params={"category": "gpu", "limit": 1}).json()[
        "items"
    ][0]
    added = client.post(f"/api/v1/products/{product['id']}/favorite", headers=auth_headers)
    assert added.status_code == 200
    favorites = client.get("/api/v1/products/favorites/me", headers=auth_headers)
    assert favorites.status_code == 200
    assert any(item["id"] == product["id"] for item in favorites.json()["items"])

    offer_id = product["offers"][0]["id"]
    history = client.get(f"/api/v1/products/offers/{offer_id}/history")
    assert history.status_code == 200
    assert history.json()["points"]


def test_product_compare(client):
    products = client.get(
        "/api/v1/products", params={"category": "cpu", "limit": 2, "in_stock": True}
    )
    assert products.status_code == 200, products.text
    items = products.json()["items"]
    assert len(items) == 2
    response = client.post(
        "/api/v1/products/compare",
        json={"product_ids": [items[0]["id"], items[1]["id"]]},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["common_category"] == "cpu"
    assert len(body["products"]) == 2
    assert body["highest_performance_product_id"] in {items[0]["id"], items[1]["id"]}
    assert isinstance(body["spec_keys"], list)


def test_product_compare_rejects_duplicate_ids(client):
    product = client.get("/api/v1/products", params={"limit": 1, "in_stock": True}).json()["items"][
        0
    ]
    response = client.post(
        "/api/v1/products/compare",
        json={"product_ids": [product["id"], product["id"]]},
    )
    assert response.status_code == 422
