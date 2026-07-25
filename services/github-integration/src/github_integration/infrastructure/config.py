from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GITHUB_INTEGRATION_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://github_integration:github_integration@localhost:5432/arp"
    auth_service_url: str = "http://auth:8000"
    regression_detection_url: str = "http://regression-detection:8000"
    upstream_timeout_seconds: float = 15.0

    github_api_base_url: str = "https://api.github.com"

    # A single static token (PAT or GitHub App installation token) for the
    # whole deployment — this self-hosted platform has no multi-tenant
    # GitHub App JWT/installation-token flow yet, so every org's checks
    # currently post through the one App installation this token belongs
    # to. Same simplification precedent as the Gateway's single dev org
    # placeholder and the Notification Service's single SMTP relay.
    github_token: str = ""

    # Shared across every org's webhook for the same reason — see above.
    github_webhook_secret: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
