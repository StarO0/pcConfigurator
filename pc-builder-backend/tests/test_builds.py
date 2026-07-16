def generate(client, prompt="Нужен тихий игровой ПК до 6000 PLN для 1440p и будущего апгрейда"):
    response = client.post(
        "/api/v1/builds/generate", json={"prompt": prompt, "basket_mode": "balanced"}
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_generate_five_distinct_private_builds(client):
    data = generate(client)
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
        assert build["access_token"]
        assert build["compatibility_status"] != "incompatible"
        assert build["bottleneck"]["status"] in {"balanced", "cpu_limited", "gpu_limited"}
        assert not any(issue["severity"] == "error" for issue in build["compatibility_issues"])
        assert len(build["components"]) == 8
        assert float(build["total_price"]) <= 6000
        assert float(build["component_price"]) + float(build["delivery_price"]) == float(
            build["total_price"]
        )
        signatures.add(tuple(item["product"]["id"] for item in build["components"]))
    assert len(signatures) == 5
    by_profile = {build["profile"]: build for build in data["builds"]}
    assert float(by_profile["economy"]["total_price"]) < float(by_profile["optimal"]["total_price"])
    amd_components = {item["category"]: item["product"] for item in by_profile["amd"]["components"]}
    assert amd_components["cpu"]["brand"] == "AMD"
    assert amd_components["gpu"]["specs"]["gpu_brand"] == "AMD"
    intel_components = {
        item["category"]: item["product"] for item in by_profile["intel_nvidia"]["components"]
    }
    assert intel_components["cpu"]["brand"] == "Intel"
    assert intel_components["gpu"]["specs"]["gpu_brand"] == "NVIDIA"

    private_build = data["builds"][0]
    denied = client.get(f"/api/v1/builds/{private_build['id']}")
    assert denied.status_code == 403
    allowed = client.get(
        f"/api/v1/builds/{private_build['id']}",
        headers={"X-Build-Token": private_build["access_token"]},
    )
    assert allowed.status_code == 200


def test_replacement_save_publish_clone_and_trash(client, auth_headers):
    generated = generate(client, "Игровой компьютер до 6000 PLN")
    build = generated["builds"][0]
    build_headers = {"X-Build-Token": build["access_token"]}
    current_gpu_id = next(
        item["product"]["id"] for item in build["components"] if item["category"] == "gpu"
    )
    options = client.get(
        f"/api/v1/builds/{build['id']}/replacement-options/gpu",
        headers=build_headers,
    )
    assert options.status_code == 200, options.text
    assert all("recommendation_group" in item for item in options.json())
    replacement = next(item for item in options.json() if item["product"]["id"] != current_gpu_id)
    patched = client.patch(
        f"/api/v1/builds/{build['id']}/components/gpu",
        headers=build_headers,
        json={
            "product_id": replacement["product"]["id"],
            "expected_version": build["version"],
            "basket_mode": "balanced",
        },
    )
    assert patched.status_code == 200, patched.text
    changed = patched.json()
    assert changed["version"] > build["version"]
    assert changed["compatibility_status"] != "incompatible"

    save_headers = {**auth_headers, **build_headers}
    saved = client.post(f"/api/v1/builds/{build['id']}/save", headers=save_headers)
    assert saved.status_code == 200, saved.text
    saved_build = saved.json()
    assert saved_build["is_saved"] is True

    published = client.patch(
        f"/api/v1/builds/{build['id']}",
        headers=auth_headers,
        json={
            "expected_version": saved_build["version"],
            "name": "Мощная сборка",
            "visibility": "unlisted",
        },
    )
    assert published.status_code == 200, published.text
    public_slug = published.json()["public_slug"]
    assert client.get(f"/api/v1/builds/public/{public_slug}").status_code == 200

    cloned = client.post(
        f"/api/v1/builds/{build['id']}/clone",
        headers=auth_headers,
        json={"name": "Копия"},
    )
    assert cloned.status_code == 201
    clone_id = cloned.json()["id"]
    deleted = client.delete(f"/api/v1/builds/{clone_id}", headers=auth_headers)
    assert deleted.status_code == 200
    restored = client.post(f"/api/v1/builds/{clone_id}/restore", headers=auth_headers)
    assert restored.status_code == 200


def test_manual_build_uses_catalog_compatibility_and_is_saved(client, auth_headers):
    generated = generate(client, "Игровой компьютер до 6000 PLN")
    components = {
        item["category"]: item["product"]["id"] for item in generated["builds"][0]["components"]
    }
    checked = client.post(
        "/api/v1/catalog/compatibility",
        json={"components": components, "language": "ru"},
    )
    assert checked.status_code == 200, checked.text
    assert checked.json()["status"] != "incompatible"

    created = client.post(
        "/api/v1/builds/manual",
        headers=auth_headers,
        json={
            "name": "Ручная тестовая сборка",
            "components": components,
            "currency": "PLN",
            "language": "ru",
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["profile"] == "manual"
    assert created.json()["is_saved"] is True
    assert len(created.json()["components"]) == 8
    saved = client.get("/api/v1/builds/saved/me/list", headers=auth_headers)
    assert any(item["id"] == created.json()["id"] for item in saved.json())
