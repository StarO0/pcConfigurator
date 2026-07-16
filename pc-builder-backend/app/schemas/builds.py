from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.analysis import BottleneckAssessment
from app.schemas.products import OfferOut, ProductOut


class BuildRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget: float = Field(default=6000, ge=1500, le=500000)
    currency: str = Field(default="PLN", min_length=3, max_length=3)
    purposes: list[
        Literal["gaming", "video_editing", "programming", "office", "streaming", "ai", "universal"]
    ] = ["universal"]
    resolution: Literal["1080p", "1440p", "4k", "8k"] | None = None
    target_fps: int | None = Field(default=None, ge=30, le=1000)
    low_noise: bool = False
    upgradeability: Literal["low", "medium", "high"] = "medium"
    rgb: bool | None = None
    case_color: str | None = Field(default=None, max_length=40)
    cpu_brand: Literal["AMD", "Intel"] | None = None
    gpu_brand: Literal["NVIDIA", "AMD", "Intel"] | None = None
    storage_gb: int = Field(default=1000, ge=500, le=64000)
    ram_gb: int = Field(default=32, ge=8, le=512)
    include_wifi: bool = False
    include_bluetooth: bool = False
    overclocking: bool = False
    preferred_stores: list[str] = Field(default_factory=list, max_length=10)
    excluded_brands: list[str] = Field(default_factory=list, max_length=20)
    max_store_count: int | None = Field(default=None, ge=1, le=8)
    workload_names: list[str] = Field(default_factory=list, max_length=20)
    language: Literal["uk", "en", "pl", "ru"] = "ru"

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()

    @property
    def purpose(self) -> str:
        return self.purposes[0] if self.purposes else "universal"


class GenerateBuildRequest(BaseModel):
    prompt: str = Field(min_length=5, max_length=4000)
    budget: float | None = Field(default=None, ge=1500, le=500000)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    basket_mode: Literal["cheapest", "fewest_stores", "balanced"] = "balanced"
    language: Literal["uk", "en", "pl", "ru"] | None = None


class ManualBuildRequest(BaseModel):
    name: str = Field(default="Своя сборка", min_length=1, max_length=160)
    components: dict[
        Literal["cpu", "motherboard", "gpu", "ram", "storage", "cooler", "case", "psu"],
        UUID,
    ] = Field(min_length=1, max_length=8)
    currency: str = Field(default="PLN", min_length=3, max_length=3)
    language: Literal["uk", "en", "pl", "ru"] = "ru"
    basket_mode: Literal["cheapest", "fewest_stores", "balanced"] = "balanced"

    @field_validator("currency")
    @classmethod
    def uppercase_manual_currency(cls, value: str) -> str:
        return value.upper()


class CompatibilityIssue(BaseModel):
    code: str
    severity: Literal["error", "warning", "info"]
    message: str
    categories: list[str]
    details: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class BuildComponentOut(BaseModel):
    category: str
    product: ProductOut
    selected_offer: OfferOut | None
    quantity: int = 1


class BuildOut(BaseModel):
    id: UUID
    profile: str
    title: str
    name: str
    prompt: str
    requirements: BuildRequirements
    explanation: str
    budget: Decimal
    currency: str
    component_price: Decimal
    delivery_price: Decimal
    total_price: Decimal
    store_count: int
    is_saved: bool
    visibility: Literal["private", "unlisted", "public"]
    public_slug: str | None
    version: int
    expires_at: datetime | None
    compatibility_status: Literal["compatible", "warning", "incompatible"]
    compatibility_issues: list[CompatibilityIssue]
    bottleneck: BottleneckAssessment | None = None
    estimated_peak_power_w: int = 0
    recommended_psu_w: int = 0
    components: list[BuildComponentOut]


class GeneratedBuildOut(BuildOut):
    access_token: str | None = None


class GenerateBuildResponse(BaseModel):
    requirements: BuildRequirements
    builds: list[GeneratedBuildOut]
    cached: bool = False


class ReplacementOption(BaseModel):
    product: ProductOut
    is_compatible: bool
    issues: list[CompatibilityIssue]
    projected_total: Decimal
    price_delta: Decimal = Decimal("0")
    performance_delta_percent: float = 0
    recommendation_group: Literal["cheaper_alternative", "smart_upgrade", "balanced", "other"] = (
        "other"
    )
    recommendation_reason: str = ""
    value_score: float = 0


class ReplaceComponentRequest(BaseModel):
    product_id: UUID
    expected_version: int = Field(ge=1)
    basket_mode: Literal["cheapest", "fewest_stores", "balanced"] = "balanced"


class BuildUpdateRequest(BaseModel):
    expected_version: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    visibility: Literal["private", "unlisted", "public"] | None = None


class CloneBuildRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)


class RepriceBuildRequest(BaseModel):
    expected_version: int = Field(ge=1)
    basket_mode: Literal["cheapest", "fewest_stores", "balanced"] = "balanced"


class BuildRevisionOut(BaseModel):
    revision: int
    reason: str
    snapshot: dict
    created_at: datetime


class BuildCompareRequest(BaseModel):
    left_id: UUID
    right_id: UUID
    left_token: str | None = Field(default=None, max_length=256)
    right_token: str | None = Field(default=None, max_length=256)


class ComponentDifference(BaseModel):
    category: str
    left_product_id: UUID | None
    left_name: str | None
    left_price: Decimal | None
    right_product_id: UUID | None
    right_name: str | None
    right_price: Decimal | None
    same_product: bool


class BuildCompareResponse(BaseModel):
    left: BuildOut
    right: BuildOut
    total_price_delta: Decimal
    delivery_price_delta: Decimal
    store_count_delta: int
    differences: list[ComponentDifference]
