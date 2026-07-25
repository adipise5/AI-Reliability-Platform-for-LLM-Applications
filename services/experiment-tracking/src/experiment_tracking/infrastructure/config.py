from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EXPERIMENT_TRACKING_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://experiment_tracking:experiment_tracking@localhost:5432/arp"
    auth_service_url: str = "http://auth:8000"
    evaluation_engine_url: str = "http://evaluation-engine:8000"
    upstream_timeout_seconds: float = 30.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
