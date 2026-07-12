from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.schemas.common import Page


class StoreOut(BaseModel):
    id: UUID
    slug: str
    name: str
    base_url: str
    country: str
    is_active: bool
    last_success_at: datetime | None = None


class OfferOut(BaseModel):
    id: UUID
    store: StoreOut
    external_id: str
    url: str
    price: Decimal
    shipping_price: Decimal
    effective_price: Decimal
    currency: str
    in_stock: bool
    stock_quantity: int | None
    fetched_at: datetime
    stale: bool = False


class PricePointOut(BaseModel):
    price: Decimal
    shipping_price: Decimal
    in_stock: bool
    recorded_at: datetime


class BenchmarkOut(BaseModel):
    workload: str
    resolution: str | None
    score: float
    unit: str
    source: str | None
    measured_at: date | None


class ProductOut(BaseModel):
    id: UUID
    category: str
    brand: str
    name: str
    sku: str
    ean: str | None
    mpn: str | None
    image_url: str | None
    release_date: date | None
    performance_score: float
    noise_score: float
    upgrade_score: float
    quality_score: float
    specs: dict[str, Any]
    status: str
    version: int
    offers: list[OfferOut]
    benchmarks: list[BenchmarkOut] = []


class ProductListResponse(Page[ProductOut]):
    pass


class ProductCreate(BaseModel):
    category: str = Field(min_length=2, max_length=40)
    brand: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=2, max_length=255)
    sku: str = Field(min_length=2, max_length=120)
    ean: str | None = Field(default=None, max_length=32)
    mpn: str | None = Field(default=None, max_length=120)
    image_url: HttpUrl | None = None
    release_date: date | None = None
    performance_score: float = Field(default=0, ge=0)
    noise_score: float = Field(default=50, ge=0, le=100)
    upgrade_score: float = Field(default=50, ge=0, le=100)
    quality_score: float = Field(default=50, ge=0, le=100)
    specs: dict[str, Any] = Field(default_factory=dict)
    status: Literal["active", "discontinued", "draft"] = "active"


class ProductUpdate(BaseModel):
    version: int = Field(ge=1)
    brand: str | None = Field(default=None, min_length=1, max_length=100)
    name: str | None = Field(default=None, min_length=2, max_length=255)
    ean: str | None = Field(default=None, max_length=32)
    mpn: str | None = Field(default=None, max_length=120)
    image_url: HttpUrl | None = None
    release_date: date | None = None
    performance_score: float | None = Field(default=None, ge=0)
    noise_score: float | None = Field(default=None, ge=0, le=100)
    upgrade_score: float | None = Field(default=None, ge=0, le=100)
    quality_score: float | None = Field(default=None, ge=0, le=100)
    specs: dict[str, Any] | None = None
    status: Literal["active", "discontinued", "draft"] | None = None
    is_active: bool | None = None


class StoreCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,78}[a-z0-9]$")
    name: str = Field(min_length=2, max_length=120)
    base_url: HttpUrl
    country: str = Field(default="PL", min_length=2, max_length=2)
    parser_type: Literal["manual", "json", "csv", "api"] = "manual"
    parser_config: dict[str, Any] = Field(default_factory=dict)


class StoreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    base_url: HttpUrl | None = None
    parser_type: Literal["manual", "json", "csv", "api"] | None = None
    parser_config: dict[str, Any] | None = None
    is_active: bool | None = None


class OfferImportItem(BaseModel):
    product_sku: str | None = Field(default=None, max_length=120)
    ean: str | None = Field(default=None, max_length=32)
    mpn: str | None = Field(default=None, max_length=120)
    title: str = Field(min_length=2, max_length=1000)
    store_slug: str = Field(min_length=2, max_length=80)
    external_id: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    price: Decimal = Field(gt=0)
    shipping_price: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="PLN", min_length=3, max_length=3)
    in_stock: bool = True
    stock_quantity: int | None = Field(default=None, ge=0)
    condition: Literal["new", "used", "refurbished"] = "new"

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class OfferImportRequest(BaseModel):
    offers: list[OfferImportItem] = Field(min_length=1, max_length=10000)
    create_unmatched_products: bool = False


class UnmatchedOffer(BaseModel):
    external_id: str
    title: str
    reason: str


class OfferImportResponse(BaseModel):
    created: int
    updated: int
    skipped: int
    unmatched: list[UnmatchedOffer] = []


class PriceHistoryResponse(BaseModel):
    offer_id: UUID
    points: list[PricePointOut]


class FavoriteResponse(BaseModel):
    product_id: UUID
    favorite: bool
