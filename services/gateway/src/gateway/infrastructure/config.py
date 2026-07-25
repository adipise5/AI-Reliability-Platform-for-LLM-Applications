"""Runtime configuration, read once at process start.

All settings are prefixed ``GATEWAY_`` so they don't collide with other
services' env vars when several run in the same Docker Compose network.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GATEWAY_", env_file=".env", extra="ignore")

    # Auth adapter selection — see ADR-0003. If `static_api_keys` is set,
    # it wins (dev/test convenience, no Auth Service needed); otherwise the
    # gateway calls the Authentication Service's introspection endpoint.
    static_api_keys: str = ""
    auth_service_url: str = "http://auth:8000"
    auth_service_timeout_seconds: float = 5.0

    anthropic_api_key: str | None = None
    anthropic_base_url: str | None = None  # None = SDK default

    openai_api_key: str | None = None
    openai_base_url: str | None = None  # None = SDK default

    gemini_api_key: str | None = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com"

    ollama_base_url: str = "http://localhost:11434"

    request_timeout_seconds: float = 60.0
    default_max_tokens: int = 1024

    # Week 5: every request emits a real OTel span, exported to the Trace
    # Collector. Unlike auth, there's no local fallback mode — the SDK's
    # BatchSpanProcessor already swallows exporter failures in the
    # background, so a Trace Collector that isn't running just means
    # dropped spans, never a broken chat request.
    trace_collector_url: str = "http://trace-collector:8000"
    trace_collector_timeout_seconds: float = 5.0

    # Week 9: usage events go to Cost Analytics over a plain, unauthenticated
    # POST (see ADR-0004's reasoning for the Trace Collector — ingestion
    # trusts the internal network the same way). Unlike tracing, this call
    # is awaited inline, not backgrounded — see ADR-0006 for the tradeoff.
    cost_analytics_url: str = "http://cost-analytics:8000"
    cost_analytics_timeout_seconds: float = 5.0

    @property
    def static_api_key_set(self) -> frozenset[str]:
        return frozenset(key.strip() for key in self.static_api_keys.split(",") if key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
