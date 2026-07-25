from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PROMPT_REGISTRY_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://prompt_registry:prompt_registry@localhost:5432/arp"
    auth_service_url: str = "http://auth:8000"
    auth_service_timeout_seconds: float = 5.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
