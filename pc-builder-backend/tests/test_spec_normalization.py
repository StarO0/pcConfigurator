from app.services.spec_normalization import normalize_specs


def test_multilingual_units_and_memory_kit_normalization():
    memory = normalize_specs(
        "ram",
        "Kingston Fury DDR5 2x16GB",
        "Kingston",
        {"Тип памяти": "DDR 5", "modules": "2 x 16 GB", "частота": "6000 MHz"},
    )
    assert memory["ram_type"] == "DDR5"
    assert memory["modules"] == 2
    assert memory["capacity_gb"] == 32

    power_supply = normalize_specs(
        "psu",
        "Quiet Power",
        "Test",
        {"Мощность": "750 Вт", "form factor": "SFX-L"},
    )
    assert power_supply["power_w"] == 750
    assert power_supply["wattage"] == 750
    assert power_supply["form_factor"] == "SFX-L"
