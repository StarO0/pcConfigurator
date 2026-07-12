from __future__ import annotations

from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.products import ProductOut


class BottleneckAssessment(BaseModel):
    status: Literal["balanced", "cpu_limited", "gpu_limited"]
    severity: Literal["none", "info", "warning", "critical"]
    limiting_component: Literal["cpu", "gpu"] | None = None
    estimated_percent: float = Field(ge=0, le=100)
    resolution: str
    cpu_score: float
    gpu_score: float
    message: str
    recommended_products: list[ProductOut] = []
    methodology: str = "relative-score-v1"


class PerformanceEstimate(BaseModel):
    workload_slug: str
    workload_name: str
    kind: Literal["game", "render", "productivity"]
    resolution: str | None = None
    settings: str | None = None
    value: float
    unit: str
    confidence: Literal["low", "medium", "high"]
    limiting_component: Literal["cpu", "gpu", "ram", "balanced"] | None = None
    source: str | None = None
    disclaimer: str


class UpsellRecommendation(BaseModel):
    category: Literal["monitor", "ups", "keyboard", "mouse", "headset"]
    product: ProductOut
    reason: str
    priority: int = Field(ge=1, le=100)
    projected_price: Decimal | None = None


class BuildAnalysisResponse(BaseModel):
    build_id: UUID
    bottleneck: BottleneckAssessment
    performance: list[PerformanceEstimate]
    upsell: list[UpsellRecommendation]
    estimated_peak_power_w: int
    recommended_psu_w: int


class WorkloadOut(BaseModel):
    slug: str
    name: str
    names: dict[str, str]
    kind: Literal["game", "render", "productivity"]
    unit: str
    lower_is_better: bool
    accelerator: Literal["cpu", "gpu", "hybrid"]
    default_resolution: str | None
    settings: str | None
    source_url: str | None


class WorkloadCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,118}[a-z0-9]$")
    names: dict[str, str]
    kind: Literal["game", "render", "productivity"]
    unit: str = Field(min_length=1, max_length=30)
    lower_is_better: bool = False
    accelerator: Literal["cpu", "gpu", "hybrid"] = "hybrid"
    default_resolution: str | None = Field(default=None, max_length=30)
    settings: str | None = Field(default=None, max_length=80)
    cpu_weight: float = Field(default=0.35, ge=0, le=1)
    gpu_weight: float = Field(default=0.65, ge=0, le=1)
    ram_requirement_gb: int = Field(default=16, ge=1, le=1024)
    source_url: str | None = Field(default=None, max_length=1000)


class BenchmarkResultImport(BaseModel):
    product_id: UUID
    workload_slug: str
    resolution: str | None = Field(default=None, max_length=30)
    score: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=30)
    source: str | None = Field(default=None, max_length=500)


class BenchmarkImportRequest(BaseModel):
    results: list[BenchmarkResultImport] = Field(min_length=1, max_length=10000)


class BenchmarkImportResponse(BaseModel):
    created: int
    updated: int
