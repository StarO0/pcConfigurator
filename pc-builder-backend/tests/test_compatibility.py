from types import SimpleNamespace

from app.services.compatibility import compatibility_engine


def product(**specs):
    return SimpleNamespace(specs=specs, sku="test")


def test_detects_multiple_hardware_conflicts():
    issues = compatibility_engine.validate(
        {
            "cpu": product(socket="AM5", peak_power_w=200),
            "motherboard": product(
                socket="LGA1700",
                ram_type="DDR5",
                form_factor="ATX",
                m2_slots=0,
                recommended_cpu_power_w=120,
                fan_headers=1,
            ),
            "ram": product(ram_type="DDR4", capacity_gb=64, modules=4),
            "gpu": product(
                length_mm=400,
                slots=4,
                peak_power_w=400,
                power_connectors=["12V-2x6"],
                recommended_psu_w=850,
            ),
            "storage": product(interface="NVMe", form_factor=2280, pcie_generation=4),
            "cooler": product(type="air", sockets=["AM4"], cooling_capacity_w=120, height_mm=180),
            "case": product(
                motherboard_form_factors=["mATX"],
                max_gpu_length_mm=300,
                max_gpu_slots=3,
                max_cooler_height_mm=160,
                psu_form_factors=["ATX"],
                included_fans=4,
            ),
            "psu": product(wattage=650, connectors=["8-pin"], form_factor="ATX"),
        }
    )
    codes = {issue.code for issue in issues}
    assert {
        "cpu_socket_mismatch",
        "ram_type_mismatch",
        "cooler_socket_mismatch",
        "gpu_too_long",
        "psu_power_low",
        "psu_connector_missing",
        "m2_slot_missing",
    } <= codes
    assert compatibility_engine.status(issues) == "incompatible"
    gpu_issue = next(issue for issue in issues if issue.code == "gpu_too_long")
    assert gpu_issue.details["difference_mm"] == 100
    assert "100" in gpu_issue.message


def test_sparse_catalog_specs_do_not_create_false_hardware_conflicts():
    issues = compatibility_engine.validate(
        {
            "cpu": product(socket="AM5", power_w=65),
            "motherboard": product(),
            "ram": product(capacity_gb=32),
            "gpu": product(length_mm=330, power_w=250),
            "storage": product(interface="NVMe"),
            "cooler": product(type="air"),
            "case": product(),
            "psu": product(),
        }
    )
    assert not any(issue.severity == "error" for issue in issues)
