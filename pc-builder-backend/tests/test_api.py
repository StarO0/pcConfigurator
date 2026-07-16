def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def create_user_and_token(client, email="daniel@example.com"):
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": "Daniel",
            "password": "strong-password-123",
        },
    )
    assert register.status_code in {201, 409}

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "strong-password-123"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def test_auth_flow(client):
    token = create_user_and_token(client)
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "daniel@example.com"


def test_generate_five_distinct_builds(client):
    response = client.post(
        "/api/v1/builds/generate",
        json={"prompt": "Нужен тихий игровой ПК до 6000 PLN для 1440p, желательно с апгрейдом"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["requirements"]["budget"] == 6000
    assert len(data["builds"]) == 5
    assert {build["profile"] for build in data["builds"]} == {
        "optimal",
        "economy",
        "upgrade_ready",
        "amd",
        "intel_nvidia",
    }

    signatures = set()
    for build in data["builds"]:
        assert build["compatibility_status"] != "incompatible"
        assert len(build["components"]) == 8
        assert float(build["total_price"]) <= 6000
        signatures.add(tuple(item["product"]["id"] for item in build["components"]))
    assert len(signatures) == 5


def test_replacement_and_save_flow(client):
    token = create_user_and_token(client, "saved-build@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    generated = client.post(
        "/api/v1/builds/generate",
        json={"prompt": "Игровой компьютер до 6000 PLN"},
        headers=headers,
    ).json()
    build = generated["builds"][0]
    build_id = build["id"]
    build_headers = {"X-Build-Token": build["access_token"]}
    current_gpu_id = next(
        item["product"]["id"] for item in build["components"] if item["category"] == "gpu"
    )

    response = client.get(
        f"/api/v1/builds/{build_id}/replacement-options/gpu", headers=build_headers
    )
    assert response.status_code == 200
    options = response.json()
    assert options
    assert all(item["is_compatible"] for item in options)

    replacement = next(
        (item for item in options if item["product"]["id"] != current_gpu_id),
        None,
    )
    assert replacement is not None
    patched = client.patch(
        f"/api/v1/builds/{build_id}/components/gpu",
        headers=build_headers,
        json={
            "product_id": replacement["product"]["id"],
            "expected_version": build["version"],
        },
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["compatibility_status"] != "incompatible"

    saved = client.post(f"/api/v1/builds/{build_id}/save", headers={**headers, **build_headers})
    assert saved.status_code == 200
    assert saved.json()["is_saved"] is True

    saved_list = client.get("/api/v1/builds/saved/me/list", headers=headers)
    assert saved_list.status_code == 200, saved_list.text
    assert any(item["id"] == build_id for item in saved_list.json())
