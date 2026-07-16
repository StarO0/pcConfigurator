from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PC Builder API"
    app_version: str = "6.1.0"
    environment: Literal["development", "test", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    secret_key: SecretStr = SecretStr("unsafe-development-secret-change-me")
    token_pepper: SecretStr = SecretStr("unsafe-token-pepper-change-me")
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    password_reset_expire_minutes: int = 30
    email_verify_expire_hours: int = 24
    jwt_algorithm: str = "HS256"

    database_url: str = "postgresql+asyncpg://pcbuilder:pcbuilder-local-change-in-production@localhost:5432/pcbuilder"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
    )
    trusted_hosts: str = "localhost,127.0.0.1,testserver"
    force_https: bool = False
    max_request_body_bytes: int = 80_000_000
    rate_limit_anonymous_per_minute: int = 60
    rate_limit_authenticated_per_minute: int = 240
    login_attempts_per_15_minutes: int = 10

    auto_create_tables: bool = True
    seed_demo_data: bool = False
    starter_snapshot_enabled: bool = True
    starter_snapshot_path: str = "data/starter-snapshot-pl-2026-07-15.json"
    demo_expose_one_time_tokens: bool = False
    admin_bootstrap_email: str | None = None
    admin_bootstrap_password: SecretStr | None = None

    ai_provider: Literal["rules", "openai", "gemini", "deepseek"] = "rules"
    ai_fallback_provider: Literal["rules", "openai", "gemini", "deepseek"] = "rules"
    ai_timeout_seconds: float = 25.0
    ai_max_retries: int = 2
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5-mini"
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-2.5-flash"
    deepseek_api_key: SecretStr | None = None
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"

    nbp_rates_url: str = "https://api.nbp.pl/api/exchangerates/tables/A?format=json"
    offer_stale_hours: int = 12
    generated_build_ttl_hours: int = 24
    default_currency: str = "PLN"
    analysis_cache_ttl_seconds: int = 1800
    analysis_max_workloads: int = 6
    upsell_recommendation_limit: int = 8

    # Public, keyless collectors. Only complete products (identity, image and a
    # current PLN offer) are published into the catalogue.
    public_collectors_enabled: bool = False
    collector_user_agent: str = "PCConfiguratorLocal/6.0"
    collector_request_timeout_seconds: float = 30.0
    collector_min_delay_seconds: float = 1.5
    collector_max_pages_per_run: int = 100
    collector_require_robots: bool = True
    harvester_scheduler_enabled: bool = False
    harvester_scheduler_interval_seconds: int = 300

    # Open Icecat's public live catalogue provides manufacturer-authorized
    # identity, images and specifications. ``openIcecat-live`` is a public shop
    # name, not a private API key.
    open_icecat_enabled: bool = True
    open_icecat_live_url: str = "https://live.icecat.biz/api/"
    open_icecat_shopname: str = "openIcecat-live"
    open_icecat_language: str = "en"
    open_icecat_timeout_seconds: float = 25.0
    open_icecat_min_delay_seconds: float = 0.2

    # Official Ceneo affiliate integration. The application does not require
    # these values and reports the source as disabled while they are absent.
    ceneo_enabled: bool = False
    ceneo_api_key: SecretStr | None = None
    ceneo_partner_id: str | None = None
    ceneo_service: Literal["partner", "premium"] = "partner"
    ceneo_search_page_size: int = 50
    ceneo_max_pages_per_query: int = 5
    ceneo_queries_csv: str = (
        "procesor,karta graficzna,płyta główna,pamięć RAM,dysk SSD,zasilacz,obudowa,chłodzenie"
    )

    frontend_url: str = "http://localhost:3000"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from_email: str = "noreply@pcbuilder.local"
    smtp_use_tls: bool = True

    sentry_dsn: str | None = None
    log_level: str = "INFO"
    log_json: bool = True
    enable_metrics: bool = True

    service_token_header: str = "X-Service-Token"
    build_access_header: str = "X-Build-Token"
    idempotency_header: str = "Idempotency-Key"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        return [host.strip() for host in self.trusted_hosts.split(",") if host.strip()]

    @property
    def secret_key_value(self) -> str:
        return self.secret_key.get_secret_value()

    @property
    def token_pepper_value(self) -> str:
        return self.token_pepper.get_secret_value()

    @property
    def ceneo_api_key_value(self) -> str | None:
        return self.ceneo_api_key.get_secret_value() if self.ceneo_api_key else None

    @property
    def ceneo_queries(self) -> list[str]:
        return [item.strip() for item in self.ceneo_queries_csv.split(",") if item.strip()]

    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url.replace("/0", "/1")

    @property
    def result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url.replace("/0", "/2")

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.environment != "test" and not self.database_url.startswith("postgresql+asyncpg://"):
            raise ValueError("Runtime DATABASE_URL must use PostgreSQL with asyncpg")
        if self.environment == "production":
            weak = {
                "unsafe-development-secret-change-me",
                "unsafe-token-pepper-change-me",
                "change-me",
            }
            secrets_to_check = (self.secret_key_value, self.token_pepper_value)
            if any(
                value in weak
                or len(value) < 32
                or value.upper().startswith(("GENERATE_", "CHANGE_", "REPLACE_"))
                for value in secrets_to_check
            ):
                raise ValueError("Production requires strong SECRET_KEY and TOKEN_PEPPER")
            if self.auto_create_tables:
                raise ValueError("AUTO_CREATE_TABLES must be false in production; use Alembic")
            if "localhost" in self.cors_origin_list:
                raise ValueError("Production CORS_ORIGINS must not contain localhost")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
