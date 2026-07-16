from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Product, WorkloadProfile
from app.schemas.analysis import PerformanceEstimate
from app.services.i18n import normalize_language

GPU_RESOLUTION_SCALE = {
    "1080p": 1.34,
    "1440p": 1.0,
    "4k": 0.56,
    "8k": 0.27,
}
CPU_RESOLUTION_SCALE = {
    "1080p": 0.94,
    "1440p": 1.0,
    "4k": 1.06,
    "8k": 1.1,
}

DISCLAIMERS = {
    "uk": "Оцінка базується на нормалізованих бенчмарках; реальний результат залежить від налаштувань, драйверів, охолодження та версії гри.",
    "en": "This estimate uses normalized benchmarks; real results vary with settings, drivers, cooling, and game version.",
    "pl": "Szacunek bazuje na znormalizowanych benchmarkach; rzeczywisty wynik zależy od ustawień, sterowników, chłodzenia i wersji gry.",
    "ru": "Оценка основана на нормализованных бенчмарках; реальный результат зависит от настроек, драйверов, охлаждения и версии игры.",
}

DEFAULT_WORKLOADS = {
    "gaming": ["cyberpunk_2077", "counter_strike_2", "fortnite"],
    "video_editing": ["premiere_pro_4k_export", "davinci_resolve_4k_export"],
    "ai": ["stable_diffusion_xl"],
    "programming": ["code_compile"],
    "universal": ["cyberpunk_2077", "premiere_pro_4k_export", "code_compile"],
}


class PerformanceService:
    async def estimate(
        self,
        session: AsyncSession,
        components: dict[str, Product],
        requirements: Any,
        limit: int = 6,
    ) -> list[PerformanceEstimate]:
        requested = self._requested_workloads(requirements)
        result = await session.execute(
            select(WorkloadProfile).where(
                WorkloadProfile.is_active.is_(True),
                WorkloadProfile.slug.in_(requested),
            )
        )
        by_slug = {item.slug: item for item in result.scalars()}
        profiles = [by_slug[slug] for slug in requested if slug in by_slug][:limit]
        return [self._estimate_one(profile, components, requirements) for profile in profiles]

    def _requested_workloads(self, requirements: Any) -> list[str]:
        explicit = [self._slugify(item) for item in getattr(requirements, "workload_names", [])]
        if explicit:
            return list(dict.fromkeys(explicit))
        selected: list[str] = []
        for purpose in getattr(requirements, "purposes", ["universal"]):
            selected.extend(DEFAULT_WORKLOADS.get(purpose, []))
        if not selected:
            selected.extend(DEFAULT_WORKLOADS["universal"])
        return list(dict.fromkeys(selected))

    def _estimate_one(
        self,
        workload: WorkloadProfile,
        components: dict[str, Product],
        requirements: Any,
    ) -> PerformanceEstimate:
        language = normalize_language(getattr(requirements, "language", "ru"))
        resolution = (
            getattr(requirements, "resolution", None)
            or workload.default_resolution
            or ("1440p" if workload.kind == "game" else None)
        )
        cpu = components.get("cpu")
        gpu = components.get("gpu")
        ram = components.get("ram")
        cpu_value = self._benchmark_value(cpu, workload.slug, workload.default_resolution)
        gpu_value = self._benchmark_value(gpu, workload.slug, workload.default_resolution)
        confidence = "high" if cpu_value is not None and gpu_value is not None else "medium"

        if workload.kind == "game":
            value, limiting = self._game_fps(
                cpu,
                gpu,
                cpu_value,
                gpu_value,
                resolution or "1440p",
            )
            value *= self._ram_factor(ram, workload.ram_requirement_gb)
            return PerformanceEstimate(
                workload_slug=workload.slug,
                workload_name=workload.names.get(language)
                or workload.names.get("en")
                or workload.slug,
                kind="game",
                resolution=resolution,
                settings=workload.settings,
                value=round(max(value, 1), 1),
                unit=workload.unit,
                confidence=confidence,
                limiting_component=limiting,
                source=workload.source_url,
                disclaimer=DISCLAIMERS[language],
            )

        value, limiting, confidence = self._non_game_value(
            workload,
            cpu,
            gpu,
            cpu_value,
            gpu_value,
        )
        ram_factor = self._ram_factor(ram, workload.ram_requirement_gb)
        if workload.lower_is_better:
            value /= max(ram_factor, 0.5)
        else:
            value *= ram_factor
        return PerformanceEstimate(
            workload_slug=workload.slug,
            workload_name=workload.names.get(language) or workload.names.get("en") or workload.slug,
            kind=workload.kind,
            resolution=resolution,
            settings=workload.settings,
            value=round(max(value, 0.1), 1),
            unit=workload.unit,
            confidence=confidence,
            limiting_component=limiting,
            source=workload.source_url,
            disclaimer=DISCLAIMERS[language],
        )

    def _game_fps(
        self,
        cpu: Product | None,
        gpu: Product | None,
        cpu_value: float | None,
        gpu_value: float | None,
        resolution: str,
    ) -> tuple[float, str]:
        if cpu_value is None:
            cpu_value = max(float(cpu.performance_score if cpu else 100) * 0.78, 30)
        if gpu_value is None:
            gpu_value = max(float(gpu.performance_score if gpu else 100) * 0.28, 20)
        cpu_ceiling = cpu_value * CPU_RESOLUTION_SCALE.get(resolution, 1.0)
        gpu_fps = gpu_value * GPU_RESOLUTION_SCALE.get(resolution, 1.0)
        if abs(cpu_ceiling - gpu_fps) / max(cpu_ceiling, gpu_fps, 1) < 0.1:
            limiting = "balanced"
        else:
            limiting = "cpu" if cpu_ceiling < gpu_fps else "gpu"
        # 2% overhead represents game engine, OS, and background tasks.
        return min(cpu_ceiling, gpu_fps) * 0.98, limiting

    def _non_game_value(
        self,
        workload: WorkloadProfile,
        cpu: Product | None,
        gpu: Product | None,
        cpu_value: float | None,
        gpu_value: float | None,
    ) -> tuple[float, str, str]:
        confidence = "high" if cpu_value is not None and gpu_value is not None else "medium"
        if cpu_value is None:
            cpu_value = self._fallback_score(cpu, workload.lower_is_better, base=360)
            confidence = "low"
        if gpu_value is None:
            gpu_value = self._fallback_score(gpu, workload.lower_is_better, base=300)
            confidence = "low"

        if workload.accelerator == "cpu":
            return cpu_value, "cpu", confidence
        if workload.accelerator == "gpu":
            return gpu_value, "gpu", confidence

        cpu_weight = max(workload.cpu_weight, 0.01)
        gpu_weight = max(workload.gpu_weight, 0.01)
        total_weight = cpu_weight + gpu_weight
        cpu_weight /= total_weight
        gpu_weight /= total_weight
        if workload.lower_is_better:
            throughput = cpu_weight / max(cpu_value, 0.01) + gpu_weight / max(gpu_value, 0.01)
            value = 1 / max(throughput, 0.0001)
            limiting = "cpu" if cpu_value > gpu_value else "gpu"
        else:
            value = cpu_value * cpu_weight + gpu_value * gpu_weight
            limiting = "cpu" if cpu_value < gpu_value else "gpu"
        if abs(cpu_value - gpu_value) / max(cpu_value, gpu_value, 1) < 0.12:
            limiting = "balanced"
        return value, limiting, confidence

    @staticmethod
    def _benchmark_value(
        product: Product | None,
        workload_slug: str,
        resolution: str | None,
    ) -> float | None:
        if not product:
            return None
        exact = None
        fallback = None
        for item in getattr(product, "benchmarks", []):
            if item.workload != workload_slug:
                continue
            fallback = float(item.score)
            if item.resolution == resolution:
                exact = float(item.score)
                break
        return exact if exact is not None else fallback

    @staticmethod
    def _fallback_score(
        product: Product | None,
        lower_is_better: bool,
        base: float,
    ) -> float:
        score = max(float(product.performance_score if product else 100), 1)
        return base * 100 / score if lower_is_better else score

    @staticmethod
    def _ram_factor(ram: Product | None, requirement_gb: int) -> float:
        if not ram:
            return 0.75
        capacity = int(ram.specs.get("capacity_gb", 0))
        if capacity >= requirement_gb:
            return min(1.08, 1 + (capacity - requirement_gb) / max(requirement_gb, 1) * 0.03)
        return max(0.55, capacity / max(requirement_gb, 1))

    @staticmethod
    def _slugify(value: str) -> str:
        return "_".join(value.strip().lower().replace("-", " ").split())


performance_service = PerformanceService()
