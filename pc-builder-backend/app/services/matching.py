import re
import unicodedata
from dataclasses import dataclass

from rapidfuzz.fuzz import token_set_ratio
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


class ProductMatcher:
    async def match(
        self,
        session: AsyncSession,
        *,
        sku: str | None,
        ean: str | None,
        mpn: str | None,
        title: str,
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
        bind = session.get_bind()
        if bind.dialect.name == "postgresql":
            result = await session.execute(
                select(Product)
                .where(Product.is_active.is_(True), Product.normalized_name.is_not(None))
                .order_by(func.similarity(Product.normalized_name, normalized).desc())
                .limit(50)
            )
        else:
            result = await session.execute(
                select(Product).where(
                    Product.is_active.is_(True), Product.normalized_name.is_not(None)
                )
            )
        best: Product | None = None
        best_score = 0.0
        for product in result.scalars():
            score = float(token_set_ratio(normalized, product.normalized_name))
            if mpn and product.mpn and normalize_text(mpn) == normalize_text(product.mpn):
                score = max(score, 98.0)
            if score > best_score:
                best, best_score = product, score
        if best is not None and best_score >= minimum_fuzzy_score:
            return ProductMatch(best, best_score, "fuzzy")
        return ProductMatch(None, best_score, "unmatched")


product_matcher = ProductMatcher()
