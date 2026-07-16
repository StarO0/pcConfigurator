import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from rapidfuzz.fuzz import token_set_ratio, token_sort_ratio
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Product

NOISE_WORDS = {
    "new",
    "nowy",
    "szt",
    "produkt",
    "karta",
    "graficzna",
    "procesor",
    "plyta",
    "główna",
    "glowna",
    "dysk",
    "ssd",
    "pamięć",
    "pamiec",
    "zasilacz",
    "obudowa",
    "chłodzenie",
    "chlodzenie",
    "monitor",
    "klawiatura",
    "mysz",
    "słuchawki",
    "sluchawki",
}

IDENTITY_SPEC_FIELDS: dict[str, tuple[str, ...]] = {
    "ram": ("capacity_gb", "ram_type", "speed_mhz", "module_count", "cas_latency", "color"),
    "gpu": ("chipset", "gpu_chip", "vram_gb", "color", "length_mm"),
    "storage": ("capacity_gb", "interface", "form_factor", "type"),
    "monitor": ("size_inches", "resolution", "refresh_rate_hz", "panel_type"),
    "motherboard": ("socket", "chipset", "ram_type", "form_factor"),
    "psu": ("wattage", "form_factor", "efficiency_rating", "modularity"),
    "case": ("form_factor", "color", "max_gpu_length_mm"),
    "cooler": ("socket", "radiator_mm", "height_mm", "color"),
    "cpu": ("socket", "cores", "threads"),
    "keyboard": ("switch_type", "layout", "color"),
    "mouse": ("sensor", "dpi", "color", "connectivity"),
}


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    tokens = [token for token in value.split() if token not in NOISE_WORDS]
    return " ".join(tokens)


@dataclass(slots=True)
class ProductMatch:
    product: Product | None
    confidence: float
    method: str


def _spec_value(value: Any) -> str | float | tuple[str, ...] | None:
    if value in (None, "", []):
        return None
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, list):
        return tuple(sorted(normalize_text(str(item)) for item in value))
    return normalize_text(str(value))


def _spec_similarity(
    category: str | None, source: dict[str, Any], candidate: dict[str, Any]
) -> tuple[float, int, int]:
    fields = IDENTITY_SPEC_FIELDS.get(category or "", ())
    matches = conflicts = evidence = 0
    for field in fields:
        left = _spec_value(source.get(field))
        right = _spec_value(candidate.get(field))
        if left is None or right is None:
            continue
        evidence += 1
        if isinstance(left, float) and isinstance(right, float):
            tolerance = max(abs(right) * 0.015, 0.5)
            equal = abs(left - right) <= tolerance
        else:
            equal = left == right
        if equal:
            matches += 1
        else:
            conflicts += 1
    score = matches * 100 / evidence if evidence else 0.0
    return score, evidence, conflicts


class ProductMatcher:
    async def match(
        self,
        session: AsyncSession,
        *,
        sku: str | None,
        ean: str | None,
        mpn: str | None,
        title: str,
        brand: str | None = None,
        category: str | None = None,
        specs: dict[str, Any] | None = None,
        minimum_fuzzy_score: float = 88,
    ) -> ProductMatch:
        direct_filters = []
        if sku:
            direct_filters.append(Product.sku == sku)
        if ean:
            direct_filters.append(Product.ean == ean)
        if mpn:
            direct_filters.append(Product.mpn == mpn)
        if direct_filters:
            result = await session.execute(select(Product).where(or_(*direct_filters)))
            matches = result.scalars().all()
            if len(matches) == 1:
                method = "sku" if sku and matches[0].sku == sku else "ean_mpn"
                return ProductMatch(matches[0], 100.0, method)
            if len(matches) > 1:
                exact_ean = next((p for p in matches if ean and p.ean == ean), None)
                if exact_ean:
                    return ProductMatch(exact_ean, 100.0, "ean")

        normalized = normalize_text(title)
        identity_filters = [Product.is_active.is_(True)]
        if category:
            identity_filters.append(Product.category == category.strip().lower())
        exact = await session.execute(
            select(Product)
            .where(
                *identity_filters,
                func.lower(Product.name) == title.strip().lower(),
            )
            .limit(5)
        )
        exact_products = list(exact.scalars())
        if len(exact_products) == 1:
            return ProductMatch(exact_products[0], 100.0, "exact_name")
        if len(exact_products) > 1:
            ranked = sorted(
                (
                    (*_spec_similarity(category, specs or {}, product.specs or {}), product)
                    for product in exact_products
                ),
                key=lambda item: (item[0], item[1], -item[2]),
                reverse=True,
            )
            top_score, top_evidence, top_conflicts, top_product = ranked[0]
            second_score = ranked[1][0] if len(ranked) > 1 else -1.0
            if (
                top_evidence >= 2
                and top_conflicts == 0
                and top_score >= 99
                and second_score < top_score
            ):
                return ProductMatch(top_product, 98.0, "exact_name_specs")
            return ProductMatch(None, 90.0, "ambiguous_variant")
        bind = session.get_bind()
        if bind.dialect.name == "postgresql":
            result = await session.execute(
                select(Product)
                .where(*identity_filters, Product.normalized_name.is_not(None))
                .order_by(func.similarity(Product.normalized_name, normalized).desc())
                .limit(50)
            )
        else:
            candidate_filters = [*identity_filters, Product.normalized_name.is_not(None)]
            if brand:
                candidate_filters.append(func.lower(Product.brand) == brand.strip().lower())
            elif not category:
                significant = next((token for token in normalized.split() if len(token) >= 3), "")
                if significant:
                    candidate_filters.append(Product.normalized_name.contains(significant))
            result = await session.execute(select(Product).where(*candidate_filters).limit(500))
        ranked_candidates: list[tuple[float, int, int, Product]] = []
        for product in result.scalars():
            set_score = float(token_set_ratio(normalized, product.normalized_name))
            sort_score = float(token_sort_ratio(normalized, product.normalized_name))
            # token_set_ratio alone considers a short subset a perfect match
            # (for example "Gaming OC" and "Radeon RX 7600 Gaming OC").
            name_score = sort_score * 0.65 + set_score * 0.35
            spec_score, evidence, conflicts = _spec_similarity(
                category, specs or {}, product.specs or {}
            )
            score = name_score
            if evidence:
                score = name_score * 0.82 + spec_score * 0.18 - conflicts * 8
            if mpn and product.mpn and normalize_text(mpn) == normalize_text(product.mpn):
                score = max(score, 98.0)
            ranked_candidates.append((score, evidence, conflicts, product))
        ranked_candidates.sort(key=lambda item: item[0], reverse=True)
        if not ranked_candidates:
            return ProductMatch(None, 0.0, "unmatched")
        best_score, best_evidence, best_conflicts, best = ranked_candidates[0]
        second_score = ranked_candidates[1][0] if len(ranked_candidates) > 1 else -1.0
        if (
            best_score >= 82
            and best_evidence >= 2
            and best_conflicts == 0
            and best_score - second_score >= 6
        ):
            return ProductMatch(best, 94.0, "fuzzy_variant_specs")
        if best_score >= minimum_fuzzy_score and best_score - second_score >= 3:
            return ProductMatch(best, best_score, "fuzzy_specs" if specs else "fuzzy")
        method = "ambiguous_variant" if best_score >= minimum_fuzzy_score else "unmatched"
        return ProductMatch(None, best_score, method)


product_matcher = ProductMatcher()
