"""Typed application configuration.

Every runtime knob is declared here as a Pydantic field with validation, so a
misconfigured deployment fails loudly at startup rather than mysteriously at
request time. Values are sourced from environment variables (and an optional
`.env` file in local development) — see `.env.example` for the full surface.

Usage::

    from core.config import get_settings

    settings = get_settings()          # cached singleton
    dsn = settings.postgres_dsn

`get_settings()` is memoized so the environment is parsed exactly once per
process. Tests can override individual fields by constructing `Settings(...)`
directly with keyword arguments.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(str, Enum):
    """Deployment environment. Drives conservative defaults (e.g. no SQL echo
    in production regardless of the DEBUG flag)."""

    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Root configuration object. One instance per process."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- Application ----------
    app_env: AppEnv = Field(default=AppEnv.LOCAL, alias="APP_ENV")
    app_name: str = Field(default="Ecommerce AI Design Director", alias="APP_NAME")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")  # noqa: S104
    api_port: int = Field(default=8000, ge=1, le=65535, alias="API_PORT")
    api_cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        alias="API_CORS_ORIGINS",
    )

    # ---------- Security ----------
    secret_key: SecretStr = Field(alias="SECRET_KEY")

    # ---------- PostgreSQL ----------
    postgres_dsn: str = Field(alias="POSTGRES_DSN")
    postgres_pool_size: int = Field(default=10, ge=1, alias="POSTGRES_POOL_SIZE")
    postgres_max_overflow: int = Field(default=20, ge=0, alias="POSTGRES_MAX_OVERFLOW")

    # ---------- Redis ----------
    redis_dsn: str = Field(default="redis://localhost:6379/0", alias="REDIS_DSN")

    # ---------- Qdrant ----------
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: SecretStr | None = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(default="design_memory", alias="QDRANT_COLLECTION")

    # ---------- LLM (Anthropic Claude) ----------
    anthropic_api_key: SecretStr = Field(alias="ANTHROPIC_API_KEY")
    llm_default_model: str = Field(default="claude-opus-4-8", alias="LLM_DEFAULT_MODEL")
    llm_fast_model: str = Field(
        default="claude-haiku-4-5-20251001", alias="LLM_FAST_MODEL"
    )
    llm_max_output_tokens: int = Field(default=8192, ge=1, alias="LLM_MAX_OUTPUT_TOKENS")
    llm_timeout_seconds: float = Field(default=120.0, gt=0, alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=3, ge=0, alias="LLM_MAX_RETRIES")

    # ---------- Figma via MCP ----------
    figma_mcp_command: str | None = Field(default=None, alias="FIGMA_MCP_COMMAND")
    figma_access_token: SecretStr | None = Field(default=None, alias="FIGMA_ACCESS_TOKEN")

    # ---------- Commerce platforms ----------
    shopify_admin_api_token: SecretStr | None = Field(
        default=None, alias="SHOPIFY_ADMIN_API_TOKEN"
    )
    shopify_store_domain: str | None = Field(default=None, alias="SHOPIFY_STORE_DOMAIN")
    magento_base_url: str | None = Field(default=None, alias="MAGENTO_BASE_URL")
    magento_access_token: SecretStr | None = Field(
        default=None, alias="MAGENTO_ACCESS_TOKEN"
    )

    # ---------- Observability ----------
    log_format: Literal["text", "json"] = Field(default="text", alias="LOG_FORMAT")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", alias="LOG_LEVEL"
    )

    # ---------- Derived / validators ----------
    @field_validator("api_cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        """Accept a comma-separated string from the environment as a list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("secret_key")
    @classmethod
    def _reject_weak_secret(cls, value: SecretStr) -> SecretStr:
        """A short secret is an operational foot-gun; refuse it at startup."""
        if len(value.get_secret_value()) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return value

    @property
    def is_production(self) -> bool:
        return self.app_env is AppEnv.PRODUCTION

    @property
    def sql_echo(self) -> bool:
        """Echo SQL only when debugging outside production."""
        return self.app_debug and not self.is_production


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton.

    Memoized so the environment is parsed once. Call `get_settings.cache_clear()`
    in tests if you need to re-read the environment.
    """
    return Settings()  # type: ignore[call-arg]  # values come from the environment
