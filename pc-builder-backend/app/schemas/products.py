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
    parser_type: str
    parser_config: dict[str, Any] = Field(default_factory=dict)
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
    source_metadata: dict[str, Any] = Field(default_factory=dict)
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
    gallery_urls: list[str] = Field(default_factory=list)
    canonical_source: str | None = None
    canonical_id: str | None = None
    source_url: str | None = None
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


class ProductCompareRequest(BaseModel):
    product_ids: list[UUID] = Field(min_length=2, max_length=4)

    @field_validator("product_ids")
    @classmethod
    def unique_products(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != len(value):
            raise ValueError("product_ids must be unique")
        return value


class ProductCompareResponse(BaseModel):
    products: list[ProductOut]
    common_category: str | None
    spec_keys: list[str]
    lowest_effective_price_product_id: UUID | None
    highest_performance_product_id: UUID | None


class ProductCreate(BaseModel):
    category: str = Field(min_length=2, max_length=40)
    brand: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=2, max_length=255)
    sku: str = Field(min_length=2, max_length=120)
    ean: str | None = Field(default=None, max_length=32)
    mpn: str | None = Field(default=None, max_length=120)
    image_url: HttpUrl | None = None
    gallery_urls: list[HttpUrl] = Field(default_factory=list, max_length=24)
    canonical_source: str | None = Field(default=None, max_length=50)
    canonical_id: str | None = Field(default=None, max_length=120)
    source_url: HttpUrl | None = None
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
    gallery_urls: list[HttpUrl] | None = Field(default=None, max_length=24)
    canonical_source: str | None = Field(default=None, max_length=50)
    canonical_id: str | None = Field(default=None, max_length=120)
    source_url: HttpUrl | None = None
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
    parser_type: Literal[
        "manual",
        "browser_snapshot",
        "json",
        "csv",
        "xml",
        "yml",
        "api",
        "html_selector",
        "jsonld_sitemap",
        "catalog_enrichment",
        "catalog_acquisition",
        "ceneo",
    ] = "manual"
    parser_config: dict[str, Any] = Field(default_factory=dict)


class StoreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    base_url: HttpUrl | None = None
    parser_type: (
        Literal[
            "manual",
            "browser_snapshot",
            "json",
            "csv",
            "xml",
            "yml",
            "api",
            "html_selector",
            "jsonld_sitemap",
            "catalog_enrichment",
            "catalog_acquisition",
            "ceneo",
        ]
        | None
    ) = None
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
    brand: str | None = Field(default=None, max_length=100)
    category: str | None = Field(default=None, max_length=40)
    image_url: HttpUrl | None = None
    specs: dict[str, Any] = Field(default_factory=dict)
    source_metadata: dict[str, Any] = Field(default_factory=dict)

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


class ProductPricePointOut(PricePointOut):
    offer_id: UUID
    store_name: str
    currency: str


class ProductPriceHistoryResponse(BaseModel):
    product_id: UUID
    points: list[ProductPricePointOut]


class FavoriteResponse(BaseModel):
    product_id: UUID
    favorite: bool


class ProductImportItem(BaseModel):
    category: str = Field(min_length=2, max_length=40)
    brand: str = Field(default="Unknown", min_length=1, max_length=100)
    name: str = Field(min_length=2, max_length=255)
    sku: str = Field(min_length=2, max_length=120)
    ean: str | None = Field(default=None, max_length=32)
    mpn: str | None = Field(default=None, max_length=120)
    image_url: HttpUrl | None = None
    gallery_urls: list[HttpUrl] = Field(default_factory=list, max_length=24)
    canonical_source: str | None = Field(default=None, max_length=50)
    canonical_id: str | None = Field(default=None, max_length=120)
    source_url: HttpUrl | None = None
    performance_score: float | None = Field(default=None, ge=0)
    specs: dict[str, Any] = Field(default_factory=dict)


class ProductImportRequest(BaseModel):
    products: list[ProductImportItem] = Field(min_length=1, max_length=20_000)
    update_existing: bool = True


class ProductImportResponse(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: list[str] = []
