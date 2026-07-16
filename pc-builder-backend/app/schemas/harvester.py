from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


class HarvestItem(BaseModel):
    product_sku: str | None = Field(default=None, max_length=120)
    ean: str | None = Field(default=None, max_length=32)
    mpn: str | None = Field(default=None, max_length=120)
    title: str = Field(min_length=2, max_length=1000)
    store_slug: str = Field(min_length=2, max_length=80)
    external_id: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    price: Decimal | None = Field(default=None, gt=0)
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


class HarvesterBatchRequest(BaseModel):
    source_slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,78}[a-z0-9]$")
    source_name: str = Field(min_length=2, max_length=120)
    source_base_url: HttpUrl
    items: list[HarvestItem] = Field(min_length=1, max_length=10_000)
    create_products: bool = True
    auto_accept: bool = True
    terms_confirmed: bool = False


class HtmlExtractionRequest(BaseModel):
    html: str = Field(min_length=20, max_length=5_000_000)
    url: HttpUrl
    store_slug: str = Field(min_length=2, max_length=80)
    selectors: dict[str, Any] = Field(default_factory=dict)


class HtmlImportRequest(HtmlExtractionRequest):
    source_name: str = Field(min_length=2, max_length=120)
    create_products: bool = True
    auto_accept: bool = True


class HarvesterImportResponse(BaseModel):
    received: int
    accepted: int
    pending: int
    rejected: int
    products_created: int
    products_updated: int
    offers_created: int
    offers_updated: int
    duplicates: int
    errors: list[str] = Field(default_factory=list)


class HarvestRecordOut(BaseModel):
    id: UUID
    store_id: UUID
    store_slug: str
    product_id: UUID | None
    source_url: str
    external_id: str | None
    status: str
    title: str | None
    brand: str | None
    category: str | None
    price: Decimal | None
    currency: str | None
    image_url: str | None
    match_confidence: float
    match_method: str
    quality_score: float
    error_message: str | None
    discovered_at: datetime
    processed_at: datetime | None


class CrawlQueueOut(BaseModel):
    id: UUID
    store_id: UUID
    store_slug: str
    url: str
    status: str
    priority: int
    attempts: int
    not_before: datetime | None
    last_http_status: int | None
    last_error: str | None
    discovered_at: datetime
    processed_at: datetime | None


class QueueUrlsRequest(BaseModel):
    store_slug: str
    urls: list[HttpUrl] = Field(min_length=1, max_length=50_000)
    priority: int = Field(default=100, ge=0, le=1000)


class HarvesterDashboardOut(BaseModel):
    records: int
    accepted: int
    pending: int
    rejected: int
    errors: int
    queued_urls: int
    products: int
    products_with_images: int
    image_coverage_percent: float
    active_offers: int
    snapshot_offers: int
    source_count: int


class HarvesterRunDueOut(BaseModel):
    checked: int
    started: int
    skipped: int
    runs: list[UUID] = Field(default_factory=list)


class EnrichmentRunRequest(BaseModel):
    pages: int = Field(default=25, ge=1, le=100)
    terms_confirmed: bool


class EnrichmentStoreOut(BaseModel):
    id: UUID
    slug: str
    name: str
    is_active: bool
    terms_confirmed: bool
    discovered_urls: int
    crawl_offset: int
    last_batch: dict[str, Any]
    last_discovery_batch: dict[str, Any]
    last_run_status: str | None
    last_error_message: str | None
    last_success_at: datetime | None
    last_error_at: datetime | None


class EnrichmentStatusOut(BaseModel):
    products: int
    products_with_images: int
    products_with_offers: int
    products_complete: int
    products_with_multiple_stores: int
    missing_images: int
    missing_offers: int
    coverage_percent: float
    pending_ambiguous: int
    stores: list[EnrichmentStoreOut]
