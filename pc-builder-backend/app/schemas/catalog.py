from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.builds import CompatibilityIssue


class CatalogSourceOut(BaseModel):
    slug: str
    name: str
    mode: str
    enabled: bool
    configured: bool
    last_success_at: str | None = None
    last_error_at: str | None = None


class CatalogStatusOut(BaseModel):
    products: int
    products_with_live_offers: int
    active_offers: int
    stores: int
    price_history_points: int
    full_catalog_loaded: bool
    sources: list[CatalogSourceOut]


class CategoryCountOut(BaseModel):
    category: str
    products: int
    products_with_offers: int


class CompatibilityCheckRequest(BaseModel):
    components: dict[
        Literal["cpu", "motherboard", "gpu", "ram", "storage", "cooler", "case", "psu"],
        UUID,
    ] = Field(min_length=1, max_length=8)
    language: Literal["ru", "uk", "pl", "en"] = "ru"


class CompatibilityCheckResponse(BaseModel):
    status: Literal["compatible", "warning", "incompatible"]
    issues: list[CompatibilityIssue]
    estimated_peak_power_w: int
    recommended_psu_w: int | None = None
