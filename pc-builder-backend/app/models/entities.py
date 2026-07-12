from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="user", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    builds: Mapped[list[Build]] = relationship(back_populates="owner")
    sessions: Mapped[list[AuthSession]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    favorites: Mapped[list[FavoriteProduct]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="sessions")


class RefreshTokenHistory(Base):
    __tablename__ = "refresh_token_history"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth_sessions.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    rotated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )


class OneTimeToken(Base):
    __tablename__ = "one_time_tokens"
    __table_args__ = (Index("ix_ott_user_purpose", "user_id", "purpose"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    purpose: Mapped[str] = mapped_column(String(40), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    base_url: Mapped[str] = mapped_column(String(1000))
    country: Mapped[str] = mapped_column(String(2), default="PL")
    parser_type: Mapped[str] = mapped_column(String(40), default="manual")
    parser_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    offers: Mapped[list[Offer]] = relationship(back_populates="store")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (Index("ix_products_category_brand", "category", "brand"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    category: Mapped[str] = mapped_column(String(40), index=True)
    brand: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    normalized_name: Mapped[str] = mapped_column(String(255), index=True)
    sku: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    ean: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    mpn: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    performance_score: Mapped[float] = mapped_column(default=0.0)
    noise_score: Mapped[float] = mapped_column(default=50.0)
    upgrade_score: Mapped[float] = mapped_column(default=50.0)
    quality_score: Mapped[float] = mapped_column(default=50.0)
    specs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    __mapper_args__ = {"version_id_col": version}

    offers: Mapped[list[Offer]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    build_components: Mapped[list[BuildComponent]] = relationship(back_populates="product")
    benchmarks: Mapped[list[ProductBenchmark]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (
        UniqueConstraint("store_id", "external_id", name="uq_offer_store_external"),
        Index("ix_offers_product_stock_currency", "product_id", "in_stock", "currency"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    store_id: Mapped[UUID] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    external_id: Mapped[str] = mapped_column(String(255))
    title_raw: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    url: Mapped[str] = mapped_column(String(1500))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    shipping_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="PLN", index=True)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    stock_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    condition: Mapped[str] = mapped_column(String(20), default="new")
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    product: Mapped[Product] = relationship(back_populates="offers")
    store: Mapped[Store] = relationship(back_populates="offers")
    price_history: Mapped[list[PriceHistory]] = relationship(
        back_populates="offer", cascade="all, delete-orphan"
    )


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (Index("ix_price_history_offer_recorded", "offer_id", "recorded_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    offer_id: Mapped[UUID] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    shipping_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )

    offer: Mapped[Offer] = relationship(back_populates="price_history")


class CurrencyRate(Base):
    __tablename__ = "currency_rates"
    __table_args__ = (UniqueConstraint("base", "quote", "rate_date", name="uq_currency_rate_day"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    base: Mapped[str] = mapped_column(String(3), index=True)
    quote: Mapped[str] = mapped_column(String(3), index=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    rate_date: Mapped[date] = mapped_column(Date, index=True)
    source: Mapped[str] = mapped_column(String(50), default="NBP")
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProductBenchmark(Base):
    __tablename__ = "product_benchmarks"
    __table_args__ = (
        UniqueConstraint("product_id", "workload", "resolution", name="uq_benchmark"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    workload: Mapped[str] = mapped_column(String(120), index=True)
    resolution: Mapped[str | None] = mapped_column(String(30), nullable=True)
    score: Mapped[float]
    unit: Mapped[str] = mapped_column(String(30), default="points")
    source: Mapped[str | None] = mapped_column(String(500), nullable=True)
    measured_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    product: Mapped[Product] = relationship(back_populates="benchmarks")


class Build(Base):
    __tablename__ = "builds"
    __table_args__ = (Index("ix_builds_owner_saved", "owner_id", "is_saved"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    access_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    public_slug: Mapped[str | None] = mapped_column(
        String(64), unique=True, nullable=True, index=True
    )
    visibility: Mapped[str] = mapped_column(String(20), default="private", index=True)
    name: Mapped[str] = mapped_column(String(160), default="Моя сборка")
    prompt: Mapped[str] = mapped_column(Text)
    profile: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(160))
    requirements: Mapped[dict[str, Any]] = mapped_column(JSON)
    explanation: Mapped[str] = mapped_column(Text, default="")
    budget: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="PLN")
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    delivery_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    store_count: Mapped[int] = mapped_column(Integer, default=0)
    is_saved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    __mapper_args__ = {"version_id_col": version}

    owner: Mapped[User | None] = relationship(back_populates="builds")
    components: Mapped[list[BuildComponent]] = relationship(
        back_populates="build", cascade="all, delete-orphan"
    )
    revisions: Mapped[list[BuildRevision]] = relationship(
        back_populates="build", cascade="all, delete-orphan"
    )


class BuildComponent(Base):
    __tablename__ = "build_components"
    __table_args__ = (UniqueConstraint("build_id", "category", name="uq_build_category"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    build_id: Mapped[UUID] = mapped_column(ForeignKey("builds.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True
    )
    selected_offer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("offers.id", ondelete="SET NULL"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    build: Mapped[Build] = relationship(back_populates="components")
    product: Mapped[Product] = relationship(back_populates="build_components")
    selected_offer: Mapped[Offer | None] = relationship(foreign_keys=[selected_offer_id])


class BuildRevision(Base):
    __tablename__ = "build_revisions"
    __table_args__ = (UniqueConstraint("build_id", "revision", name="uq_build_revision"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    build_id: Mapped[UUID] = mapped_column(ForeignKey("builds.id", ondelete="CASCADE"), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    reason: Mapped[str] = mapped_column(String(120), default="update")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    build: Mapped[Build] = relationship(back_populates="revisions")


class FavoriteProduct(Base):
    __tablename__ = "favorite_products"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_favorite_product"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="favorites")
    product: Mapped[Product] = relationship()


class ParserRun(Base):
    __tablename__ = "parser_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    store_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("stores.id", ondelete="SET NULL"), nullable=True, index=True
    )
    task_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="running", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ServiceToken(Base):
    __tablename__ = "service_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_service_token_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("service_tokens.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(120), index=True)
    resource_type: Mapped[str] = mapped_column(String(80), index=True)
    resource_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )


class PriceAlert(Base):
    __tablename__ = "price_alerts"
    __table_args__ = (UniqueConstraint("user_id", "product_id", "currency", name="uq_price_alert"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    target_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="PLN")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_notified_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    last_notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )


class AIUsage(Base):
    __tablename__ = "ai_usage"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(40), index=True)
    model: Mapped[str] = mapped_column(String(120))
    operation: Mapped[str] = mapped_column(String(60), index=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int]
    succeeded: Mapped[bool] = mapped_column(Boolean, default=True)
    error_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
