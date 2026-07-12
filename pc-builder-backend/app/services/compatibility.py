from __future__ import annotations

import math
from typing import Any

from app.schemas.builds import CompatibilityIssue
from app.services.i18n import compatibility_message, normalize_language


class CompatibilityEngine:
    def validate(
        self,
        components: dict[str, Any],
        language: str | None = None,
    ) -> list[CompatibilityIssue]:
        issues: list[CompatibilityIssue] = []
        cpu = components.get("cpu")
        motherboard = components.get("motherboard")
        gpu = components.get("gpu")
        ram = components.get("ram")
        storage = components.get("storage")
        psu = components.get("psu")
        case = components.get("case")
        cooler = components.get("cooler")

        self._cpu_motherboard(cpu, motherboard, issues)
        self._memory(motherboard, ram, cooler, issues)
        self._cooling(cpu, motherboard, cooler, case, ram, issues)
        self._case(motherboard, gpu, psu, case, cooler, issues)
        self._power(cpu, gpu, psu, issues)
        self._storage(motherboard, storage, issues)
        self._headers(motherboard, case, issues)

        lang = normalize_language(language)
        for issue in issues:
            issue.message = compatibility_message(
                issue.code,
                lang,
                issue.details,
                fallback=issue.message,
            )
        return issues

    def _cpu_motherboard(self, cpu, motherboard, issues: list[CompatibilityIssue]) -> None:
        if not cpu or not motherboard:
            return
        cpu_socket = cpu.specs.get("socket")
        board_socket = motherboard.specs.get("socket")
        if cpu_socket != board_socket:
            issues.append(
                self._error(
                    "cpu_socket_mismatch",
                    "Сокеты CPU и платы не совпадают.",
                    ["cpu", "motherboard"],
                    {"cpu_socket": cpu_socket, "motherboard_socket": board_socket},
                )
            )
        supported_cpus = motherboard.specs.get("supported_cpu_skus", [])
        if supported_cpus and cpu.sku not in supported_cpus:
            issues.append(
                self._error(
                    "cpu_not_in_support_list",
                    "Плата не заявляет поддержку этого процессора.",
                    ["cpu", "motherboard"],
                    {"cpu_sku": cpu.sku},
                )
            )
        min_bios = cpu.specs.get("min_bios")
        board_bios = motherboard.specs.get("bios_version")
        if (
            min_bios
            and board_bios
            and self._version_tuple(board_bios) < self._version_tuple(min_bios)
        ):
            issues.append(
                self._error(
                    "bios_update_required",
                    "Для процессора требуется обновление BIOS.",
                    ["cpu", "motherboard"],
                    {"required": min_bios, "current": board_bios},
                )
            )
        cpu_power = float(cpu.specs.get("peak_power_w", cpu.specs.get("power_w", 0)))
        vrm_limit = float(motherboard.specs.get("recommended_cpu_power_w", 9999))
        if cpu_power > vrm_limit:
            issues.append(
                self._error(
                    "vrm_insufficient",
                    "Подсистема питания платы слишком слабая для CPU под полной нагрузкой.",
                    ["cpu", "motherboard"],
                    {"cpu_power_w": cpu_power, "board_limit_w": vrm_limit},
                )
            )
        if cpu.specs.get("overclockable") and not motherboard.specs.get("cpu_overclocking", False):
            issues.append(
                self._warning(
                    "cpu_overclocking_unavailable",
                    "Разгон CPU на этой плате недоступен.",
                    ["cpu", "motherboard"],
                )
            )

    def _memory(self, motherboard, ram, cooler, issues: list[CompatibilityIssue]) -> None:
        if not motherboard or not ram:
            return
        if motherboard.specs.get("ram_type") != ram.specs.get("ram_type"):
            issues.append(
                self._error(
                    "ram_type_mismatch",
                    "Тип памяти не поддерживается платой.",
                    ["motherboard", "ram"],
                    {
                        "required": motherboard.specs.get("ram_type"),
                        "actual": ram.specs.get("ram_type"),
                    },
                )
            )
        modules = int(ram.specs.get("modules", 1))
        slots = int(motherboard.specs.get("ram_slots", 4))
        if modules > slots:
            issues.append(
                self._error(
                    "not_enough_ram_slots",
                    "Модулей RAM больше, чем слотов на плате.",
                    ["motherboard", "ram"],
                    {"modules": modules, "slots": slots},
                )
            )
        capacity = int(ram.specs.get("capacity_gb", 0))
        max_capacity = int(motherboard.specs.get("max_ram_gb", 9999))
        if capacity > max_capacity:
            issues.append(
                self._error(
                    "ram_capacity_too_high",
                    "Объём RAM превышает максимум платы.",
                    ["motherboard", "ram"],
                    {"capacity_gb": capacity, "max_capacity_gb": max_capacity},
                )
            )
        speed = int(ram.specs.get("speed_mhz", 0))
        max_speed = int(motherboard.specs.get("max_ram_speed_mhz", 99999))
        if speed > max_speed:
            issues.append(
                self._warning(
                    "ram_speed_downclock",
                    "Память будет работать на более низкой частоте, поддерживаемой платой.",
                    ["motherboard", "ram"],
                    {"ram_mhz": speed, "board_mhz": max_speed},
                )
            )
        if bool(ram.specs.get("ecc", False)) and not bool(
            motherboard.specs.get("ecc_support", False)
        ):
            issues.append(
                self._error(
                    "ecc_not_supported",
                    "ECC-память не поддерживается платой.",
                    ["motherboard", "ram"],
                )
            )
        if cooler and ram.specs.get("height_mm") and cooler.specs.get("max_ram_height_mm"):
            height = float(ram.specs["height_mm"])
            available = float(cooler.specs["max_ram_height_mm"])
            if height > available:
                issues.append(
                    self._warning(
                        "ram_cooler_clearance",
                        "Высокие модули RAM могут конфликтовать с кулером.",
                        ["ram", "cooler"],
                        {
                            "required_mm": height,
                            "available_mm": available,
                            "difference_mm": round(height - available, 1),
                        },
                    )
                )

    def _cooling(
        self, cpu, motherboard, cooler, case, ram, issues: list[CompatibilityIssue]
    ) -> None:
        del motherboard, ram
        if not cpu or not cooler:
            return
        socket = cpu.specs.get("socket")
        if socket not in cooler.specs.get("sockets", []):
            issues.append(
                self._error(
                    "cooler_socket_mismatch",
                    "Кулер не поддерживает сокет CPU.",
                    ["cpu", "cooler"],
                    {"socket": socket},
                )
            )
        cpu_power = float(cpu.specs.get("peak_power_w", cpu.specs.get("power_w", 0)))
        capacity = float(cooler.specs.get("cooling_capacity_w", 0))
        if capacity < cpu_power:
            issues.append(
                self._error(
                    "cooler_capacity_low",
                    "Кулер не справится с пиковым тепловыделением CPU.",
                    ["cpu", "cooler"],
                    {"required_w": cpu_power, "capacity_w": capacity},
                )
            )
        elif capacity < cpu_power * 1.2:
            issues.append(
                self._warning(
                    "cooler_low_headroom",
                    "У кулера небольшой запас; под нагрузкой система может быть шумной.",
                    ["cpu", "cooler"],
                    {"required_w": cpu_power, "capacity_w": capacity},
                )
            )
        if cooler.specs.get("type") == "aio" and case:
            radiator = int(cooler.specs.get("radiator_mm", 0))
            supported = case.specs.get("radiator_support_mm", [])
            if radiator and radiator not in supported:
                issues.append(
                    self._error(
                        "radiator_not_supported",
                        "Корпус не поддерживает радиатор этой СЖО.",
                        ["cooler", "case"],
                        {"radiator_mm": radiator, "supported": ", ".join(map(str, supported))},
                    )
                )

    def _case(self, motherboard, gpu, psu, case, cooler, issues: list[CompatibilityIssue]) -> None:
        if not case:
            return
        if motherboard and motherboard.specs.get("form_factor") not in case.specs.get(
            "motherboard_form_factors", []
        ):
            issues.append(
                self._error(
                    "motherboard_case_mismatch",
                    "Форм-фактор платы не поддерживается корпусом.",
                    ["motherboard", "case"],
                    {
                        "form_factor": motherboard.specs.get("form_factor"),
                        "supported": ", ".join(case.specs.get("motherboard_form_factors", [])),
                    },
                )
            )
        if gpu:
            gpu_length = float(gpu.specs.get("length_mm", 0))
            max_length = float(case.specs.get("max_gpu_length_mm", 0))
            if gpu_length > max_length:
                issues.append(
                    self._error(
                        "gpu_too_long",
                        "Видеокарта не помещается по длине.",
                        ["gpu", "case"],
                        {
                            "required_mm": gpu_length,
                            "available_mm": max_length,
                            "difference_mm": round(gpu_length - max_length, 1),
                            "conflict_object": "drive_cage_or_front_radiator",
                        },
                    )
                )
            if cooler and cooler.specs.get("type") == "aio":
                radiator = int(cooler.specs.get("radiator_mm", 0))
                front_sizes = set(case.specs.get("front_radiator_support_mm", []))
                top_sizes = set(case.specs.get("top_radiator_support_mm", []))
                front_clearance = case.specs.get("max_gpu_length_with_front_radiator_mm")
                forced_front = radiator in front_sizes and radiator not in top_sizes
                if forced_front and front_clearance and gpu_length > float(front_clearance):
                    issues.append(
                        self._error(
                            "gpu_front_radiator_conflict",
                            "Видеокарта конфликтует с передним радиатором.",
                            ["gpu", "cooler", "case"],
                            {
                                "required_mm": gpu_length,
                                "available_mm": float(front_clearance),
                                "difference_mm": round(gpu_length - float(front_clearance), 1),
                                "radiator_mm": radiator,
                            },
                        )
                    )
            gpu_height = float(gpu.specs.get("height_mm", 0))
            max_height = float(case.specs.get("max_gpu_height_mm", 9999))
            if gpu_height > max_height:
                issues.append(
                    self._error(
                        "gpu_too_tall",
                        "Видеокарта не помещается по высоте.",
                        ["gpu", "case"],
                        {
                            "required_mm": gpu_height,
                            "available_mm": max_height,
                            "difference_mm": round(gpu_height - max_height, 1),
                        },
                    )
                )
            gpu_slots = float(gpu.specs.get("slots", 2))
            max_slots = float(case.specs.get("max_gpu_slots", 9))
            if gpu_slots > max_slots:
                issues.append(
                    self._error(
                        "gpu_too_thick",
                        "Видеокарта занимает больше слотов, чем допускает корпус.",
                        ["gpu", "case"],
                        {
                            "required_slots": gpu_slots,
                            "available_slots": max_slots,
                            "difference_slots": round(gpu_slots - max_slots, 1),
                        },
                    )
                )
        if cooler and cooler.specs.get("type", "air") == "air":
            height = float(cooler.specs.get("height_mm", 0))
            available = float(case.specs.get("max_cooler_height_mm", 0))
            if height > available:
                issues.append(
                    self._error(
                        "cooler_too_tall",
                        "Башенный кулер не помещается в корпус.",
                        ["cooler", "case"],
                        {
                            "required_mm": height,
                            "available_mm": available,
                            "difference_mm": round(height - available, 1),
                        },
                    )
                )
        if psu:
            if psu.specs.get("form_factor", "ATX") not in case.specs.get(
                "psu_form_factors", ["ATX"]
            ):
                issues.append(
                    self._error(
                        "psu_form_factor_mismatch",
                        "Форм-фактор БП не поддерживается корпусом.",
                        ["psu", "case"],
                        {
                            "form_factor": psu.specs.get("form_factor", "ATX"),
                            "supported": ", ".join(case.specs.get("psu_form_factors", [])),
                        },
                    )
                )
            length = float(psu.specs.get("length_mm", 0))
            available = float(case.specs.get("max_psu_length_mm", 9999))
            if length > available:
                issues.append(
                    self._error(
                        "psu_too_long",
                        "Блок питания не помещается в корпус.",
                        ["psu", "case"],
                        {
                            "required_mm": length,
                            "available_mm": available,
                            "difference_mm": round(length - available, 1),
                        },
                    )
                )

    def _power(self, cpu, gpu, psu, issues: list[CompatibilityIssue]) -> None:
        if not cpu or not gpu or not psu:
            return
        required = self.required_psu_w(cpu, gpu)
        if int(psu.specs.get("wattage", 0)) < required:
            issues.append(
                self._error(
                    "psu_power_low",
                    f"Нужен БП минимум примерно {required} Вт.",
                    ["cpu", "gpu", "psu"],
                    {"required_w": required, "actual_w": int(psu.specs.get("wattage", 0))},
                )
            )
        required_connectors = list(gpu.specs.get("power_connectors", []))
        available = list(psu.specs.get("connectors", []))
        remaining = list(available)
        missing: list[str] = []
        for connector in required_connectors:
            if connector in remaining:
                remaining.remove(connector)
            else:
                missing.append(connector)
        if missing:
            issues.append(
                self._error(
                    "psu_connector_missing",
                    "У БП нет необходимых разъёмов GPU.",
                    ["gpu", "psu"],
                    {"missing": ", ".join(missing)},
                )
            )
        if gpu.specs.get("requires_atx_3") and not psu.specs.get("atx_3", False):
            issues.append(
                self._warning(
                    "atx3_recommended",
                    "Для этой видеокарты предпочтителен БП стандарта ATX 3.x.",
                    ["gpu", "psu"],
                )
            )
        efficiency = str(psu.specs.get("efficiency", ""))
        if "Bronze" in efficiency and required > 700:
            issues.append(
                self._warning(
                    "psu_quality_headroom",
                    "Для мощной сборки лучше БП класса Gold и выше.",
                    ["psu"],
                )
            )

    def _storage(self, motherboard, storage, issues: list[CompatibilityIssue]) -> None:
        if not motherboard or not storage:
            return
        interface = storage.specs.get("interface")
        if interface == "NVMe":
            if int(motherboard.specs.get("m2_slots", 0)) < 1:
                issues.append(
                    self._error(
                        "m2_slot_missing",
                        "На плате нет M.2 для NVMe.",
                        ["motherboard", "storage"],
                    )
                )
            size = int(storage.specs.get("form_factor", 2280))
            if size not in motherboard.specs.get("m2_sizes", [2280]):
                issues.append(
                    self._error(
                        "m2_size_unsupported",
                        "Форм-фактор M.2 не поддерживается платой.",
                        ["motherboard", "storage"],
                        {"required": size},
                    )
                )
            drive_pcie = int(storage.specs.get("pcie_generation", 3))
            board_pcie = int(motherboard.specs.get("m2_pcie_generation", 3))
            if drive_pcie > board_pcie:
                issues.append(
                    self._info(
                        "storage_pcie_downshift",
                        "SSD будет работать на скорости более старой версии PCIe.",
                        ["motherboard", "storage"],
                        {"drive_generation": drive_pcie, "board_generation": board_pcie},
                    )
                )
        if interface == "SATA" and int(motherboard.specs.get("sata_ports", 0)) < 1:
            issues.append(
                self._error(
                    "sata_port_missing",
                    "На плате нет доступного SATA-порта.",
                    ["motherboard", "storage"],
                )
            )

    def _headers(self, motherboard, case, issues: list[CompatibilityIssue]) -> None:
        if not motherboard or not case:
            return
        if case.specs.get("front_usb_c") and not motherboard.specs.get("front_usb_c_header"):
            issues.append(
                self._warning(
                    "front_usb_c_unavailable",
                    "Передний USB-C корпуса нельзя подключить к этой плате.",
                    ["motherboard", "case"],
                )
            )
        required_fan_headers = int(case.specs.get("included_fans", 0))
        fan_headers = int(motherboard.specs.get("fan_headers", 1))
        if required_fan_headers > fan_headers and not case.specs.get("fan_hub", False):
            issues.append(
                self._warning(
                    "fan_headers_low",
                    "Для всех вентиляторов понадобится разветвитель или хаб.",
                    ["motherboard", "case"],
                    {"required": required_fan_headers, "available": fan_headers},
                )
            )

    @staticmethod
    def required_psu_w(cpu: Any, gpu: Any) -> int:
        cpu_power = float(cpu.specs.get("peak_power_w", cpu.specs.get("power_w", 0)))
        gpu_power = float(gpu.specs.get("peak_power_w", gpu.specs.get("power_w", 0)))
        calculated = math.ceil((cpu_power + gpu_power + 100) * 1.25 / 50) * 50
        vendor_recommended = int(gpu.specs.get("recommended_psu_w", 0))
        return max(calculated, vendor_recommended)

    @staticmethod
    def estimated_peak_power_w(components: dict[str, Any]) -> int:
        cpu = components.get("cpu")
        gpu = components.get("gpu")
        base = 100
        if cpu:
            base += int(cpu.specs.get("peak_power_w", cpu.specs.get("power_w", 0)))
        if gpu:
            base += int(gpu.specs.get("peak_power_w", gpu.specs.get("power_w", 0)))
        return base

    @staticmethod
    def status(issues: list[CompatibilityIssue]) -> str:
        if any(issue.severity == "error" for issue in issues):
            return "incompatible"
        if any(issue.severity == "warning" for issue in issues):
            return "warning"
        return "compatible"

    @staticmethod
    def _issue(
        code: str,
        severity: str,
        message: str,
        categories: list[str],
        details: dict | None = None,
    ) -> CompatibilityIssue:
        return CompatibilityIssue(
            code=code,
            severity=severity,
            message=message,
            categories=categories,
            details=details or {},
        )

    def _error(
        self, code: str, message: str, categories: list[str], details: dict | None = None
    ) -> CompatibilityIssue:
        return self._issue(code, "error", message, categories, details)

    def _warning(
        self, code: str, message: str, categories: list[str], details: dict | None = None
    ) -> CompatibilityIssue:
        return self._issue(code, "warning", message, categories, details)

    def _info(
        self, code: str, message: str, categories: list[str], details: dict | None = None
    ) -> CompatibilityIssue:
        return self._issue(code, "info", message, categories, details)

    @staticmethod
    def _version_tuple(value: str) -> tuple[int, ...]:
        return tuple(
            int(part)
            for part in "".join(
                char if char.isdigit() or char == "." else "." for char in value
            ).split(".")
            if part.isdigit()
        )


compatibility_engine = CompatibilityEngine()
