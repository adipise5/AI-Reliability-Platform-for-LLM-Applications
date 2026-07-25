from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REPORT_GENERATOR_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://report_generator:report_generator@localhost:5432/arp"
    redis_url: str = "redis://localhost:6379/0"

    auth_service_url: str = "http://auth:8000"
    experiment_tracking_url: str = "http://experiment-tracking:8000"
    upstream_timeout_seconds: float = 30.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
