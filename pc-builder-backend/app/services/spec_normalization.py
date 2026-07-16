from __future__ import annotations

import re
from typing import Any

NORMALIZATION_VERSION = 2

ALIASES = {
    "socket_type": "socket",
    "cpu_socket": "socket",
    "memory_type": "ram_type",
    "memory_generation": "ram_type",
    "memory_slots": "ram_slots",
    "max_memory": "max_ram_gb",
    "memory_max": "max_ram_gb",
    "tdp": "power_w",
    "power": "power_w",
    "wattage_w": "wattage",
    "length": "length_mm",
    "gpu_length": "length_mm",
    "max_video_card_length": "max_gpu_length_mm",
    "max_gpu_length": "max_gpu_length_mm",
    "max_cpu_cooler_height": "max_cooler_height_mm",
    "height": "height_mm",
    "capacity": "capacity_gb",
    "memory": "vram_gb",
    "formfactor": "form_factor",
    "motherboard_form_factor": "form_factor",
    "pcie": "pcie_version",
    "сокет": "socket",
    "разъем": "socket",
    "тип_памяти": "ram_type",
    "слоты_памяти": "ram_slots",
    "максимум_памяти": "max_ram_gb",
    "мощность": "power_w",
    "тдп": "power_w",
    "длина": "length_mm",
    "высота": "height_mm",
    "емкость": "capacity_gb",
    "ёмкость": "capacity_gb",
    "объем": "capacity_gb",
    "объём": "capacity_gb",
    "форм_фактор": "form_factor",
    "gniazdo": "socket",
    "typ_pamięci": "ram_type",
    "moc": "power_w",
    "pojemność": "capacity_gb",
    "pojemnosc": "capacity_gb",
    "pojemność_całkowita": "capacity_gb",
    "pojemnosc_calkowita": "capacity_gb",
    "taktowanie": "speed_mhz",
    "częstotliwość_pracy": "speed_mhz",
    "czestotliwosc_pracy": "speed_mhz",
    "opóźnienie": "cas_latency",
    "opoznienie": "cas_latency",
    "opóźnienia": "cas_latency",
    "opoznienia": "cas_latency",
    "liczba_modułów": "module_count",
    "liczba_modulow": "module_count",
    "łączna_pojemność_pamięci": "capacity_gb",
    "laczna_pojemnosc_pamieci": "capacity_gb",
    "pamięć": "vram_gb",
    "pamiec": "vram_gb",
    "pamięć_ram": "vram_gb",
    "pamiec_ram": "vram_gb",
    "częstotliwość_odświeżania_ekranu": "refresh_rate_hz",
    "czestotliwosc_odswiezania_ekranu": "refresh_rate_hz",
    "przekątna_ekranu": "size_inches",
    "przekatna_ekranu": "size_inches",
    "rozdzielczość_ekranu": "resolution",
    "rozdzielczosc_ekranu": "resolution",
    "moc_znamionowa_zasilacza": "wattage",
    "standard_zasilacza": "form_factor",
    "format": "form_factor",
    "interfejs": "interface",
    "złącze": "interface",
    "zlacze": "interface",
    "kolor": "color",
}


def _key(value: str) -> str:
    result: list[str] = []
    separator = False
    for character in value.strip().lower():
        if character.isalnum():
            result.append(character)
            separator = False
        elif not separator:
            result.append("_")
            separator = True
    return "".join(result).strip("_")


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[,;/|]+", value) if item.strip()]
    return []


def _form_factor(value: Any) -> str:
    normalized = re.sub(r"[^A-Z0-9]", "", str(value).upper())
    return {
        "MATX": "mATX",
        "MICROATX": "mATX",
        "MINIITX": "Mini-ITX",
        "EATX": "E-ATX",
    }.get(normalized, str(value).upper())


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:[.,]\d+)?", value.replace(" ", ""))
        if match:
            try:
                return float(match.group().replace(",", "."))
            except ValueError:
                return None
    return None


def _integer(value: Any) -> int | None:
    number = _number(value)
    return round(number) if number is not None else None


def _ram_type(value: Any, name: str) -> str | None:
    combined = f"{value or ''} {name}".upper()
    match = re.search(r"DDR\s*([345])", combined)
    return f"DDR{match.group(1)}" if match else None


def _socket(category: str, current: Any, name: str, brand: str) -> str | None:
    combined = f"{current or ''} {name}".upper().replace(" ", "")
    known = re.search(r"(AM[345]|LGA(?:1151|1200|1700|1851|2066)|TR4|STRX4)", combined)
    if known:
        return known.group(1)
    if category != "cpu":
        return str(current).upper() if current else None
    if "RYZEN" in combined:
        series = re.search(r"RYZEN(?:[3579])?(\d{4})", combined)
        if series:
            return "AM5" if int(series.group(1)) >= 7000 else "AM4"
    if brand.upper() == "INTEL" or "COREI" in combined or "COREULTRA" in combined:
        if "COREULTRA" in combined or re.search(r"\b(?:2[4-9]|3\d)\d{3}[A-Z]*\b", combined):
            return "LGA1851"
        return "LGA1700"
    return str(current).upper() if current else None


def _pcie_generation(value: Any) -> int | None:
    if isinstance(value, (int, float)):
        return max(1, min(7, int(value)))
    match = re.search(r"(?:PCIE|PCI EXPRESS|GEN)\s*([1-7])", str(value).upper())
    if match:
        return int(match.group(1))
    match = re.search(r"([1-7])\.0", str(value))
    return int(match.group(1)) if match else None


def normalize_specs(category: str, name: str, brand: str, raw: dict[str, Any]) -> dict[str, Any]:
    specs: dict[str, Any] = {}
    for raw_key, value in (raw or {}).items():
        key = ALIASES.get(_key(str(raw_key)), _key(str(raw_key)))
        if key and value not in (None, ""):
            specs[key] = value

    socket = _socket(category, specs.get("socket"), name, brand)
    if socket:
        specs["socket"] = socket

    ram_type = _ram_type(specs.get("ram_type"), name)
    if ram_type:
        specs["ram_type"] = ram_type

    integer_fields = {
        "capacity_gb",
        "vram_gb",
        "ram_slots",
        "max_ram_gb",
        "speed_mhz",
        "wattage",
        "power_w",
        "peak_power_w",
        "recommended_psu_w",
        "length_mm",
        "height_mm",
        "max_gpu_length_mm",
        "max_cooler_height_mm",
        "module_count",
        "cas_latency",
        "refresh_rate_hz",
        "size_inches",
    }
    for field in integer_fields:
        if field in specs:
            parsed = _integer(specs[field])
            if parsed is not None:
                specs[field] = parsed

    if category == "ram":
        modules = specs.get("modules") or specs.get("kit")
        count: int | None = None
        size: int | None = None
        if isinstance(modules, list) and len(modules) >= 2:
            count, size = _integer(modules[0]), _integer(modules[1])
        elif isinstance(modules, str):
            match = re.search(r"(\d+)\s*[xх×]\s*(\d+)", modules.lower())
            if match:
                count, size = int(match.group(1)), int(match.group(2))
        else:
            count = _integer(modules)
        if count:
            specs["modules"] = count
            specs["module_count"] = count
        if count and size:
            specs["module_size_gb"] = size
            specs["capacity_gb"] = count * size
        title_kit = re.search(r"(\d+)\s*[xх×]\s*(\d+)\s*GB", name, re.IGNORECASE)
        if title_kit:
            specs.setdefault("module_count", int(title_kit.group(1)))
            specs.setdefault("modules", int(title_kit.group(1)))
            specs.setdefault("module_size_gb", int(title_kit.group(2)))
            specs.setdefault("capacity_gb", int(title_kit.group(1)) * int(title_kit.group(2)))
        title_speed = re.search(
            r"\b(2133|2400|2666|2800|2933|3000|3200|3333|3466|3600|4000|\d{4})\s*MHz\b",
            name,
            re.IGNORECASE,
        )
        if title_speed:
            specs.setdefault("speed_mhz", int(title_speed.group(1)))
        title_latency = re.search(r"\bCL\s*(\d{1,2})\b", name, re.IGNORECASE)
        if title_latency:
            specs.setdefault("cas_latency", int(title_latency.group(1)))
        title_capacity = re.search(r"\b(\d{1,3})\s*GB\b", name, re.IGNORECASE)
        if title_capacity:
            specs.setdefault("capacity_gb", int(title_capacity.group(1)))
    if category == "storage" and "capacity_gb" in specs:
        capacity = _integer(specs["capacity_gb"])
        if capacity and capacity < 32 and "tb" in str(raw).lower():
            specs["capacity_gb"] = capacity * 1000
    if category == "storage" and "capacity_gb" not in specs:
        title_capacity = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(TB|GB)\b", name, re.IGNORECASE)
        if title_capacity:
            amount = float(title_capacity.group(1).replace(",", "."))
            specs["capacity_gb"] = round(
                amount * 1000 if title_capacity.group(2).upper() == "TB" else amount
            )
    if category == "gpu":
        chipset = f"{specs.get('chipset', '')} {name}".upper()
        if "RTX" in chipset or "GEFORCE" in chipset:
            specs["gpu_brand"] = "NVIDIA"
        elif "RADEON" in chipset or re.search(r"\bRX\s*\d", chipset):
            specs["gpu_brand"] = "AMD"
    if category == "psu" and "wattage" not in specs:
        if specs.get("power_w"):
            specs["wattage"] = specs["power_w"]
        else:
            match = re.search(r"\b(\d{3,4})\s*W\b", name.upper())
            if match:
                specs["wattage"] = int(match.group(1))

    for field in (
        "sockets",
        "connectors",
        "power_connectors",
        "motherboard_form_factors",
        "psu_form_factors",
    ):
        if field in specs:
            values = _string_list(specs[field])
            if values:
                if field == "motherboard_form_factors":
                    values = [_form_factor(item) for item in values]
                elif field in {"sockets", "psu_form_factors"}:
                    values = [item.upper() for item in values]
                specs[field] = values

    if "form_factor" in specs:
        specs["form_factor"] = _form_factor(specs["form_factor"])

    pcie_source = (
        specs.get("pcie_generation") or specs.get("pcie_version") or specs.get("interface")
    )
    generation = _pcie_generation(pcie_source)
    if generation:
        specs["pcie_generation"] = generation

    specs["normalization_version"] = NORMALIZATION_VERSION
    return specs
