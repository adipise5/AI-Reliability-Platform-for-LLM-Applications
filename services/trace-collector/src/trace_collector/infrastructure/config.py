"""Runtime configuration.

No auth-service settings here, deliberately — see the README's "Auth"
section: ingestion and query are both open in this MVP, same class of
"trusted internal network" reasoning as the Auth Service's own
`/introspect` endpoint.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRACE_COLLECTOR_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://trace_collector:trace_collector@localhost:5432/arp"


@lru_cache
def get_settings() -> Settings:
    return Settings()
