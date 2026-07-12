from uuid import UUID


def generate(client, prompt, language=None):
    payload = {"prompt": prompt, "basket_mode": "balanced"}
    if language:
        payload["language"] = language
    response = client.post("/api/v1/builds/generate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_multilingual_generation_and_analysis(client):
    data = generate(
        client,
        "Potrzebuję cichy komputer do gier do 6000 PLN w 1440p, z możliwością rozbudowy",
    )
    assert data["requirements"]["language"] == "pl"
    assert len(data["builds"]) == 5
    titles = {item["title"] for item in data["builds"]}
    assert "Optymalny wybór" in titles
    assert "Maksymalna oszczędność" in titles

    build = data["builds"][0]
    response = client.get(
        f"/api/v1/builds/{build['id']}/analysis",
        headers={"X-Build-Token": build["access_token"]},
    )
    assert response.status_code == 200, response.text
    analysis = response.json()
    assert analysis["performance"]
    assert any(item["kind"] == "game" for item in analysis["performance"])
    assert analysis["upsell"]
    assert {item["category"] for item in analysis["upsell"]} & {"monitor", "ups"}
    assert analysis["recommended_psu_w"] > 0
    assert analysis["estimated_peak_power_w"] > 0


def test_workload_catalog_and_admin_benchmark_import(client, admin_headers):
    workloads = client.get("/api/v1/benchmarks/workloads", params={"language": "uk"})
    assert workloads.status_code == 200, workloads.text
    assert len(workloads.json()) >= 7
    assert any(item["slug"] == "cyberpunk_2077" for item in workloads.json())

    created = client.post(
        "/api/v1/benchmarks/admin/workloads",
        headers=admin_headers,
        json={
            "slug": "test_workload_v1",
            "names": {"en": "Test workload", "pl": "Testowe obciążenie"},
            "kind": "productivity",
            "unit": "points",
            "lower_is_better": False,
            "accelerator": "cpu",
            "cpu_weight": 1,
            "gpu_weight": 0,
            "ram_requirement_gb": 16,
        },
    )
    assert created.status_code == 201, created.text

    product = client.get("/api/v1/products", params={"category": "cpu", "limit": 1}).json()[
        "items"
    ][0]
    imported = client.post(
        "/api/v1/benchmarks/admin/results/import",
        headers=admin_headers,
        json={
            "results": [
                {
                    "product_id": product["id"],
                    "workload_slug": "test_workload_v1",
                    "resolution": None,
                    "score": 123.4,
                    "unit": "points",
                    "source": "test-suite",
                }
            ]
        },
    )
    assert imported.status_code == 200, imported.text
    assert imported.json()["created"] == 1
    UUID(product["id"])
