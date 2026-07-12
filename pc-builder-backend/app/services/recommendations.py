from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Offer, Product
from app.schemas.analysis import UpsellRecommendation
from app.services.compatibility import compatibility_engine
from app.services.i18n import normalize_language, text
from app.services.pricing import best_product_price
from app.services.serializers import product_to_schema


class RecommendationService:
    def classify_replacement(
        self,
        current_product: Product,
        candidate: Product,
        current_total: Decimal,
        projected_total: Decimal,
        language: str | None,
    ) -> tuple[str, str, float, Decimal, float]:
        lang = normalize_language(language)
        current_perf = max(float(current_product.performance_score), 1.0)
        candidate_perf = float(candidate.performance_score)
        perf_delta = (candidate_perf / current_perf - 1) * 100
        price_delta = projected_total - current_total
        value_score = candidate_perf / max(float(projected_total), 1) * 100

        if price_delta < Decimal("-20") and perf_delta >= -10:
            group = "cheaper_alternative"
            reason = text("replacement_cheaper", lang)
        elif perf_delta >= 10 and price_delta <= max(
            Decimal("350"), current_total * Decimal("0.12")
        ):
            group = "smart_upgrade"
            reason = text("replacement_upgrade", lang)
        elif perf_delta >= -5:
            group = "balanced"
            reason = text("replacement_balanced", lang)
        else:
            group = "other"
            reason = text("replacement_balanced", lang)
        return group, reason, round(perf_delta, 1), price_delta, round(value_score, 3)

    async def upsell(
        self,
        session: AsyncSession,
        components: dict[str, Product],
        requirements: Any,
        currency: str,
        limit: int = 8,
    ) -> list[UpsellRecommendation]:
        result = await session.execute(
            select(Product)
            .options(
                selectinload(Product.offers).selectinload(Offer.store),
                selectinload(Product.benchmarks),
            )
            .where(
                Product.category.in_(["monitor", "ups", "keyboard", "mouse", "headset"]),
                Product.is_active.is_(True),
                Product.status == "active",
            )
        )
        language = normalize_language(getattr(requirements, "language", "ru"))
        ranked: list[tuple[float, UpsellRecommendation]] = []
        for product in result.scalars().unique():
            price = best_product_price(product, currency)
            if price is None:
                continue
            fit, reason_key = self._upsell_fit(product, components, requirements)
            if fit <= 0:
                continue
            ranked.append(
                (
                    fit,
                    UpsellRecommendation(
                        category=product.category,
                        product=product_to_schema(product),
                        reason=text(reason_key, language),
                        priority=max(1, min(100, round(fit))),
                        projected_price=price,
                    ),
                )
            )
        ranked.sort(key=lambda item: (-item[0], item[1].projected_price or Decimal("0")))

        # Keep variety: at most two recommendations per category.
        counts: dict[str, int] = {}
        output: list[UpsellRecommendation] = []
        for _, recommendation in ranked:
            if counts.get(recommendation.category, 0) >= 2:
                continue
            counts[recommendation.category] = counts.get(recommendation.category, 0) + 1
            output.append(recommendation)
            if len(output) >= limit:
                break
        return output

    def _upsell_fit(
        self,
        product: Product,
        components: dict[str, Product],
        requirements: Any,
    ) -> tuple[float, str]:
        if product.category == "monitor":
            target_resolution = getattr(requirements, "resolution", None) or "1440p"
            target_fps = int(getattr(requirements, "target_fps", None) or 120)
            resolution = str(product.specs.get("resolution", ""))
            refresh = int(product.specs.get("refresh_hz", 60))
            score = 30.0
            if resolution == target_resolution:
                score += 35
            elif target_resolution == "4k" and resolution == "1440p":
                score += 12
            score += min(refresh / max(target_fps, 60), 1.2) * 25
            panel = str(product.specs.get("panel", "")).upper()
            if panel in {"IPS", "OLED", "QD-OLED"}:
                score += 8
            return score, "upsell_monitor"

        if product.category == "ups":
            peak_power = compatibility_engine.estimated_peak_power_w(components)
            capacity = int(product.specs.get("output_w", 0))
            if capacity < peak_power * 1.1:
                return 0, "upsell_ups"
            headroom = min(capacity / max(peak_power, 1), 2.0)
            return 55 + headroom * 20, "upsell_ups"

        # Generic peripherals are ranked by quality and value.
        return (
            35 + product.quality_score * 0.45 + product.performance_score * 0.15,
            "upsell_peripheral",
        )


recommendation_service = RecommendationService()
