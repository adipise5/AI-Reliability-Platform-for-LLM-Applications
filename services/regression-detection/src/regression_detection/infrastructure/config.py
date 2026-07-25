from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REGRESSION_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://regression:regression@localhost:5432/arp"
    auth_service_url: str = "http://auth:8000"
    evaluation_engine_url: str = "http://evaluation-engine:8000"
    trace_collector_url: str = "http://trace-collector:8000"
    upstream_timeout_seconds: float = 30.0

    # How many standard deviations below a prompt's historical mean score
    # counts as a fail / a "needs review" — see EvaluateRunUseCase.
    fail_threshold_stddev: float = 2.0
    review_threshold_stddev: float = 1.0

    # Latency-anomaly check tuning — see CheckLatencyAnomalyUseCase.
    latency_anomaly_stddev_threshold: float = 2.0
    latency_anomaly_recent_count: int = 5
    latency_anomaly_minimum_baseline_size: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
