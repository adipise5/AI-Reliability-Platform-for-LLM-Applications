from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NOTIFICATION_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://notifications:notifications@localhost:5432/arp"
    redis_url: str = "redis://localhost:6379/0"

    auth_service_url: str = "http://auth:8000"
    upstream_timeout_seconds: float = 15.0

    # SMTP relay used by the "email" channel type. Defaults point at a
    # local dev relay (e.g. MailHog) — there's no real mail provider this
    # self-hosted platform can assume, so operators configure their own.
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = False
    smtp_from_address: str = "ai-reliability-platform@localhost"


@lru_cache
def get_settings() -> Settings:
    return Settings()
