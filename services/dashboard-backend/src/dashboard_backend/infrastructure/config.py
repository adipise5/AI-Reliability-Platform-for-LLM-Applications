"""Settings for a service with no database of its own — just the auth
service and every read-facing service it fans out to."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DASHBOARD_", env_file=".env", extra="ignore")

    auth_service_url: str = "http://auth:8000"
    evaluation_engine_url: str = "http://evaluation-engine:8000"
    cost_analytics_url: str = "http://cost-analytics:8000"
    regression_detection_url: str = "http://regression-detection:8000"
    report_generator_url: str = "http://report-generator:8000"
    notification_service_url: str = "http://notification-service:8000"
    github_integration_url: str = "http://github-integration:8000"
    trace_collector_url: str = "http://trace-collector:8000"
    upstream_timeout_seconds: float = 15.0

    # The React Dashboard (Week 15) is the only browser client this
    # service expects. Vite's default dev port.
    cors_allowed_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
