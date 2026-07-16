from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Offer, Product
from app.schemas.analysis import BottleneckAssessment
from app.services.compatibility import compatibility_engine
from app.services.i18n import normalize_language, text

CPU_REQUIREMENT_RATIO = {
    "1080p": 0.66,
    "1440p": 0.54,
    "4k": 0.40,
    "8k": 0.30,
}


class BottleneckService:
    def assess(
        self,
        components: dict[str, Any],
        resolution: str | None,
        language: str | None,
    ) -> BottleneckAssessment:
        lang = normalize_language(language)
        resolution = resolution or "1440p"
        cpu = components.get("cpu")
        gpu = components.get("gpu")
        if not cpu or not gpu:
            return BottleneckAssessment(
                status="balanced",
                severity="none",
                estimated_percent=0,
                resolution=resolution,
                cpu_score=float(getattr(cpu, "performance_score", 0) or 0),
                gpu_score=float(getattr(gpu, "performance_score", 0) or 0),
                message=text("bottleneck_balanced", lang, resolution=resolution),
            )

        cpu_score = max(float(cpu.performance_score), 1.0)
        gpu_score = max(float(gpu.performance_score), 1.0)
        required_cpu = gpu_score * CPU_REQUIREMENT_RATIO.get(resolution, 0.54)
        cpu_shortfall = max(0.0, 1.0 - cpu_score / max(required_cpu, 1.0)) * 100

        ideal_gpu = cpu_score / CPU_REQUIREMENT_RATIO.get(resolution, 0.54)
        gpu_shortfall = max(0.0, 1.0 - gpu_score / max(ideal_gpu, 1.0)) * 100

        if cpu_shortfall >= 10:
            percent = round(min(cpu_shortfall, 80), 1)
            severity = "critical" if percent >= 35 else "warning" if percent >= 20 else "info"
            return BottleneckAssessment(
                status="cpu_limited",
                severity=severity,
                limiting_component="cpu",
                estimated_percent=percent,
                resolution=resolution,
                cpu_score=cpu_score,
                gpu_score=gpu_score,
                message=text("bottleneck_cpu", lang, percent=round(percent), resolution=resolution),
            )

        # A GPU limit is normal in games. Report it only if the CPU is far stronger.
        if gpu_shortfall >= 22:
            percent = round(min(gpu_shortfall, 80), 1)
            return BottleneckAssessment(
                status="gpu_limited",
                severity="info",
                limiting_component="gpu",
                estimated_percent=percent,
                resolution=resolution,
                cpu_score=cpu_score,
                gpu_score=gpu_score,
                message=text("bottleneck_gpu", lang, percent=round(percent), resolution=resolution),
            )

        return BottleneckAssessment(
            status="balanced",
            severity="none",
            estimated_percent=round(max(cpu_shortfall, gpu_shortfall), 1),
            resolution=resolution,
            cpu_score=cpu_score,
            gpu_score=gpu_score,
            message=text("bottleneck_balanced", lang, resolution=resolution),
        )

    async def assess_with_recommendations(
        self,
        session: AsyncSession,
        components: dict[str, Product],
        resolution: str | None,
        language: str | None,
        currency: str,
        limit: int = 3,
    ) -> BottleneckAssessment:
        assessment = self.assess(components, resolution, language)
        if assessment.limiting_component not in {"cpu", "gpu"}:
            return assessment

        category = assessment.limiting_component
        current = components.get(category)
        if current is None:
            return assessment

        result = await session.execute(
            select(Product)
            .options(
                selectinload(Product.offers).selectinload(Offer.store),
                selectinload(Product.benchmarks),
            )
            .where(
                Product.category == category,
                Product.is_active.is_(True),
                Product.status == "active",
                Product.performance_score > current.performance_score * 1.08,
            )
            .order_by(Product.performance_score.asc())
            .limit(50)
        )
        recommendations: list[Product] = []
        for candidate in result.scalars().unique():
            candidate_map = dict(components)
            candidate_map[category] = candidate
            issues = compatibility_engine.validate(candidate_map, language)
            if any(issue.severity == "error" for issue in issues):
                continue
            if not any(
                offer.is_active and offer.in_stock and offer.currency == currency
                for offer in candidate.offers
            ):
                continue
            new_assessment = self.assess(candidate_map, resolution, language)
            if new_assessment.estimated_percent >= assessment.estimated_percent:
                continue
            recommendations.append(candidate)
            if len(recommendations) >= limit:
                break
        from app.services.serializers import product_to_schema

        assessment.recommended_products = [product_to_schema(item) for item in recommendations]
        return assessment


bottleneck_service = BottleneckService()
