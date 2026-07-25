from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EVAL_ENGINE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://eval_engine:eval_engine@localhost:5432/arp"
    redis_url: str = "redis://localhost:6379/0"

    auth_service_url: str = "http://auth:8000"
    prompt_registry_url: str = "http://prompt-registry:8000"
    dataset_mgmt_url: str = "http://dataset-management:8000"
    gateway_url: str = "http://gateway:8000"
    hallucination_service_url: str = "http://hallucination-detection:8000"
    upstream_timeout_seconds: float = 30.0

    # Model used by the "llm_judge" scorer to grade other models' output.
    judge_model: str = "claude-sonnet-5"


@lru_cache
def get_settings() -> Settings:
    return Settings()
