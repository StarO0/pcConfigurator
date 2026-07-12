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
