"""Runtime configuration, read once at process start.

Prefixed ``AUTH_`` — see the equivalent note in the gateway's config.py.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AUTH_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://auth:auth@localhost:5432/arp"

    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_ttl_seconds: int = 3600

    # "live" in production, "test" for keys meant for CI/sandbox use — pure
    # labeling, both are validated identically today.
    api_key_environment: str = "live"

    # The React Dashboard (Week 15) calls /auth/login and /orgs directly
    # from the browser — every other service it needs goes through the
    # Dashboard Backend BFF instead. Vite's default dev port.
    cors_allowed_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
