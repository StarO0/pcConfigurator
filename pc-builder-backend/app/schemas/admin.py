from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ServiceTokenCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    scopes: list[str] = Field(default_factory=lambda: ["offers:write"])
    expires_at: datetime | None = None


class ServiceTokenCreated(BaseModel):
    id: UUID
    name: str
    token: str
    scopes: list[str]
    expires_at: datetime | None


class ParserRunOut(BaseModel):
    id: UUID
    store_id: UUID | None
    task_id: str | None
    status: str
    started_at: datetime
    finished_at: datetime | None
    created_count: int
    updated_count: int
    skipped_count: int
    error_count: int
    error_message: str | None
    metadata_json: dict[str, Any]


class AuditLogOut(BaseModel):
    id: UUID
    actor_user_id: UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    request_id: str | None
    ip_address: str | None
    details: dict[str, Any]
    created_at: datetime


class MergeProductsRequest(BaseModel):
    source_product_id: UUID
    target_product_id: UUID


class TaskQueuedResponse(BaseModel):
    task_id: str
    status: str = "queued"


class AdminUserUpdate(BaseModel):
    role: str | None = Field(default=None, pattern="^(user|admin)$")
    is_active: bool | None = None
    is_verified: bool | None = None


class AdminStatsOut(BaseModel):
    users: int
    products: int
    active_offers: int
    saved_builds: int
    stale_offers: int
    failed_parser_runs_24h: int
