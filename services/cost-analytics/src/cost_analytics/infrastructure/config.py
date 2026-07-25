"""Runtime configuration.

Ingestion (`POST /api/v1/usage-events`) is open, same "trusted internal
network" reasoning as the Trace Collector (ADR-0004) — it's the Gateway
calling it, not a user. The read endpoints (usage summary, budget) *are*
auth-protected and org-scoped, unlike the Trace Collector: this service
tracks real per-tenant financial data from day one, which is exactly the
kind of thing worth protecting even at this stage.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COST_ANALYTICS_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://cost_analytics:cost_analytics@localhost:5432/arp"
    auth_service_url: str = "http://auth:8000"
    auth_service_timeout_seconds: float = 5.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
