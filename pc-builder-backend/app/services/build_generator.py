from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import generate_opaque_token, token_hash
from app.models.entities import Build, BuildComponent, Offer, Product
from app.schemas.builds import BuildRequirements
from app.services.ai.service import ai_service
from app.services.compatibility import compatibility_engine
from app.services.pricing import BasketMode, best_product_price, optimize_basket

CATEGORY_ORDER = ["cpu", "motherboard", "gpu", "ram", "storage", "cooler", "case", "psu"]

PROFILES: dict[str, dict[str, float | str]] = {
    "max_performance": {
        "title": "Максимум производительности",
        "performance": 1.8,
        "value": 0.45,
        "noise": 0.15,
        "upgrade": 0.25,
        "quality": 0.35,
        "budget_use": 1.4,
    },
    "balanced": {
        "title": "Сбалансированная сборка",
        "performance": 1.05,
        "value": 1.0,
        "noise": 0.55,
        "upgrade": 0.55,
        "quality": 0.8,
        "budget_use": 0.9,
    },
    "quiet": {
        "title": "Тихая сборка",
        "performance": 0.8,
        "value": 0.65,
        "noise": 1.8,
        "upgrade": 0.4,
        "quality": 1.0,
        "budget_use": 0.72,
    },
    "upgrade_ready": {
        "title": "Основа для будущего апгрейда",
        "performance": 0.75,
        "value": 0.65,
        "noise": 0.35,
        "upgrade": 1.9,
        "quality": 0.85,
        "budget_use": 0.8,
    },
    "best_value": {
        "title": "Лучшее цена/качество",
        "performance": 0.9,
        "value": 1.9,
        "noise": 0.25,
        "upgrade": 0.4,
        "quality": 0.55,
        "budget_use": 0.4,
    },
}

CATEGORY_IMPORTANCE = {
    "cpu": 1.35,
    "motherboard": 0.55,
    "gpu": 1.8,
    "ram": 0.65,
    "storage": 0.45,
    "cooler": 0.35,
    "case": 0.3,
    "psu": 0.5,
}


@dataclass(slots=True)
class Candidate:
    product: Product
    price: Decimal


@dataclass(slots=True)
class State:
    components: dict[str, Candidate]
    estimated_total: Decimal
    score: float

    @property
    def signature(self) -> tuple[str, ...]:
        return tuple(str(self.components[key].product.id) for key in CATEGORY_ORDER)


@dataclass(slots=True)
class GeneratedBuild:
    build: Build
    access_token: str


class BuildGenerator:
    beam_width = 500
    max_candidates_per_category = 18

    async def generate(
        self,
        session: AsyncSession,
        prompt: str,
        requirements: BuildRequirements,
        basket_mode: BasketMode,
        owner_id: Any | None = None,
    ) -> list[GeneratedBuild]:
        candidates = await self._load_candidates(session, requirements)
        missing = [category for category in CATEGORY_ORDER if not candidates.get(category)]
        if missing:
            raise ValueError(f"Нет доступных товаров в категориях: {', '.join(missing)}")

        used_signatures: set[tuple[str, ...]] = set()
        selected: list[tuple[str, State]] = []
        for profile_name, profile in PROFILES.items():
            states = self._search_profile(candidates, requirements, profile)
            chosen = next(
                (state for state in states if state.signature not in used_signatures), None
            )
            if chosen:
                used_signatures.add(chosen.signature)
                selected.append((profile_name, chosen))

        if not selected:
            minimum = self._minimum_possible_total(candidates)
            raise ValueError(
                f"Не удалось собрать совместимый ПК. Минимум по текущему каталогу: примерно "
                f"{minimum:.2f} {requirements.currency}."
            )

        generated: list[GeneratedBuild] = []
        for profile_name, state in selected:
            products = {
                category: candidate.product for category, candidate in state.components.items()
            }
            basket = optimize_basket(
                products,
                requirements.currency,
                mode=basket_mode,
                max_store_count=requirements.max_store_count,
            )
            if basket is None or basket.total_price > Decimal(str(requirements.budget)):
                continue
            summary = [
                {
                    "category": category,
                    "name": product.name,
                    "price": float(basket.offers[category].price),
                    "specs": product.specs,
                }
                for category, product in products.items()
            ]
            explanation = await ai_service.explain_build(
                requirements,
                profile_name,
                summary,
                float(basket.total_price),
                session=session,
                user_id=owner_id,
            )
            raw_access_token = generate_opaque_token(32)
            build = Build(
                owner_id=owner_id,
                access_token_hash=token_hash(raw_access_token),
                prompt=prompt,
                profile=profile_name,
                title=str(PROFILES[profile_name]["title"]),
                name=str(PROFILES[profile_name]["title"]),
                requirements=requirements.model_dump(mode="json"),
                explanation=explanation,
                budget=Decimal(str(requirements.budget)),
                currency=requirements.currency.upper(),
                total_price=basket.total_price,
                delivery_price=basket.delivery_price,
                store_count=basket.store_count,
                is_saved=False,
                expires_at=datetime.now(UTC) + timedelta(hours=settings.generated_build_ttl_hours),
            )
            session.add(build)
            await session.flush()
            for category, product in products.items():
                session.add(
                    BuildComponent(
                        build_id=build.id,
                        category=category,
                        product_id=product.id,
                        selected_offer_id=basket.offers[category].id,
                    )
                )
            generated.append(GeneratedBuild(build=build, access_token=raw_access_token))
        await session.commit()
        if len(generated) < 3:
            raise ValueError(
                "Каталог слишком мал или бюджет слишком низкий для нескольких разных сборок"
            )
        return generated

    async def _load_candidates(
        self,
        session: AsyncSession,
        requirements: BuildRequirements,
    ) -> dict[str, list[Candidate]]:
        result = await session.execute(
            select(Product)
            .options(
                selectinload(Product.offers).selectinload(Offer.store),
                selectinload(Product.benchmarks),
            )
            .where(Product.is_active.is_(True), Product.status == "active")
        )
        grouped: dict[str, list[Candidate]] = {category: [] for category in CATEGORY_ORDER}
        excluded = {item.lower() for item in requirements.excluded_brands}
        for product in result.scalars().unique():
            if product.category not in grouped or product.brand.lower() in excluded:
                continue
            if not self._matches_requirements(product, requirements):
                continue
            price = best_product_price(product, requirements.currency)
            if price is not None:
                grouped[product.category].append(Candidate(product, price))

        for category, values in grouped.items():
            values.sort(
                key=lambda item: (
                    -(item.product.performance_score + item.product.quality_score * 0.25),
                    item.price,
                )
            )
            # Keep both top-performing and cheapest candidates.
            cheapest = sorted(values, key=lambda item: item.price)[:8]
            merged: list[Candidate] = []
            seen_ids = set()
            for candidate in [*values[: self.max_candidates_per_category], *cheapest]:
                if candidate.product.id in seen_ids:
                    continue
                seen_ids.add(candidate.product.id)
                merged.append(candidate)
            grouped[category] = merged[: self.max_candidates_per_category]
        return grouped

    def _matches_requirements(self, product: Product, req: BuildRequirements) -> bool:
        specs = product.specs
        if product.category == "cpu" and req.cpu_brand and product.brand != req.cpu_brand:
            return False
        if product.category == "gpu" and req.gpu_brand and specs.get("gpu_brand") != req.gpu_brand:
            return False
        if product.category == "ram" and int(specs.get("capacity_gb", 0)) < req.ram_gb:
            return False
        if product.category == "storage" and int(specs.get("capacity_gb", 0)) < req.storage_gb:
            return False
        if product.category == "motherboard":
            if req.include_wifi and not specs.get("wifi"):
                return False
            if req.include_bluetooth and not specs.get("bluetooth"):
                return False
            if req.overclocking and not specs.get("cpu_overclocking"):
                return False
        if product.category == "case" and req.case_color:
            color = str(specs.get("color", "")).lower()
            if color and req.case_color.lower() not in color:
                return False
        return True

    def _search_profile(
        self,
        candidates: dict[str, list[Candidate]],
        requirements: BuildRequirements,
        profile: dict[str, float | str],
    ) -> list[State]:
        budget = Decimal(str(requirements.budget))
        states = [State({}, Decimal("0"), 0.0)]
        for category in CATEGORY_ORDER:
            new_states: list[State] = []
            for state in states:
                for candidate in candidates[category]:
                    total = state.estimated_total + candidate.price
                    # Shipping can add some cost; leave a small buffer.
                    if total > budget * Decimal("1.03"):
                        continue
                    components = {**state.components, category: candidate}
                    product_map = {key: value.product for key, value in components.items()}
                    issues = compatibility_engine.validate(product_map)
                    if any(issue.severity == "error" for issue in issues):
                        continue
                    score = state.score + self._score_candidate(
                        candidate, category, requirements, profile, budget
                    )
                    score -= sum(6 for issue in issues if issue.severity == "warning")
                    new_states.append(State(components, total, score))
            if not new_states:
                return []
            new_states.sort(key=lambda item: item.score, reverse=True)
            deduped: list[State] = []
            signatures: set[tuple[str, ...]] = set()
            for state in new_states:
                partial_signature = tuple(
                    str(state.components[key].product.id)
                    for key in CATEGORY_ORDER
                    if key in state.components
                )
                if partial_signature in signatures:
                    continue
                signatures.add(partial_signature)
                deduped.append(state)
                if len(deduped) >= self.beam_width:
                    break
            states = deduped
        final = [state for state in states if state.estimated_total <= budget]
        final.sort(key=lambda item: item.score, reverse=True)
        return final

    def _score_candidate(
        self,
        candidate: Candidate,
        category: str,
        req: BuildRequirements,
        profile: dict[str, float | str],
        budget: Decimal,
    ) -> float:
        product = candidate.product
        importance = CATEGORY_IMPORTANCE[category]
        value_score = product.performance_score / max(float(candidate.price), 1) * 100
        score = importance * (
            product.performance_score * float(profile["performance"])
            + value_score * float(profile["value"])
            + product.noise_score * float(profile["noise"])
            + product.upgrade_score * float(profile["upgrade"])
            + product.quality_score * float(profile["quality"])
        )
        budget_ratio = float(candidate.price / budget)
        score += budget_ratio * 100 * float(profile["budget_use"])

        purposes = set(req.purposes)
        if category == "gpu":
            if "gaming" in purposes:
                resolution_multiplier = {"1080p": 0.85, "1440p": 1.1, "4k": 1.35, "8k": 1.5}.get(
                    req.resolution, 1.0
                )
                score += product.performance_score * 0.55 * resolution_multiplier
            if "video_editing" in purposes or "ai" in purposes:
                score += float(product.specs.get("vram_gb", 0)) * 5
                if product.specs.get("gpu_brand") == "NVIDIA":
                    score += 25
        if category == "cpu":
            if purposes & {"video_editing", "programming", "streaming", "ai"}:
                score += float(product.specs.get("cores", 0)) * 5
        if category in {"cooler", "case", "psu"} and req.low_noise:
            score += product.noise_score * 0.8
        if category in {"cpu", "motherboard", "psu", "case"} and req.upgradeability == "high":
            score += product.upgrade_score * 0.8
        if category == "gpu" and req.target_fps:
            score += product.performance_score * min(req.target_fps / 60, 3.0) * 0.12
        if req.workload_names:
            requested = {item.strip().lower() for item in req.workload_names}
            for benchmark in product.benchmarks:
                workload = benchmark.workload.strip().lower()
                if workload in requested or any(item in workload for item in requested):
                    score += min(float(benchmark.score), 2000.0) * 0.03
        return score

    @staticmethod
    def _minimum_possible_total(candidates: dict[str, list[Candidate]]) -> Decimal:
        return sum(
            (min(items, key=lambda item: item.price).price for items in candidates.values()),
            Decimal("0"),
        )


build_generator = BuildGenerator()
