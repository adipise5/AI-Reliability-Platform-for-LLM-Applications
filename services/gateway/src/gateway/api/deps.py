"""Dependency wiring: constructs use cases from concrete adapters.

This is the one module allowed to know about every concrete adapter. Route
handlers only ever see `RouteChatUseCase` / `StreamChatUseCase` / `AuthContext`
— never a provider SDK or a settings object directly. Swapping an adapter
(e.g. the Week 2 auth adapter from ADR-0003) means editing this file only.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Tracer

from gateway.application.route_chat import RouteChatUseCase
from gateway.application.stream_chat import StreamChatUseCase
from gateway.domain.entities import AuthContext, Provider
from gateway.domain.errors import AuthenticationError, AuthServiceUnavailableError
from gateway.domain.ports import AuthPort, LLMProviderPort, ProviderRegistry
from gateway.infrastructure.auth.remote_auth_adapter import RemoteAuthServiceAdapter
from gateway.infrastructure.auth.static_key_auth import StaticAPIKeyAuthAdapter
from gateway.infrastructure.config import get_settings
from gateway.infrastructure.cost_analytics_usage_sink import HttpCostAnalyticsUsageSink
from gateway.infrastructure.observability.otel_tracing_sink import OtelTracingSink
from gateway.infrastructure.observability.trace_collector_exporter import TraceCollectorSpanExporter
from gateway.infrastructure.provider_registry import ModelPrefixProviderRegistry
from gateway.infrastructure.providers.anthropic_provider import AnthropicProvider
from gateway.infrastructure.providers.gemini_provider import GeminiProvider
from gateway.infrastructure.providers.ollama_provider import OllamaProvider
from gateway.infrastructure.providers.openai_provider import OpenAIProvider

_bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def _build_provider_registry() -> ProviderRegistry:
    settings = get_settings()
    providers: dict[Provider, LLMProviderPort] = {
        Provider.OLLAMA: OllamaProvider(settings.ollama_base_url, timeout=settings.request_timeout_seconds),
    }
    if settings.anthropic_api_key:
        providers[Provider.ANTHROPIC] = AnthropicProvider(
            settings.anthropic_api_key,
            base_url=settings.anthropic_base_url,
            timeout=settings.request_timeout_seconds,
        )
    if settings.openai_api_key:
        providers[Provider.OPENAI] = OpenAIProvider(
            settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.request_timeout_seconds,
        )
    if settings.gemini_api_key:
        providers[Provider.GEMINI] = GeminiProvider(
            settings.gemini_api_key,
            base_url=settings.gemini_base_url,
            timeout=settings.request_timeout_seconds,
        )
    return ModelPrefixProviderRegistry(providers)


@lru_cache
def _build_auth_adapter() -> AuthPort:
    settings = get_settings()
    if settings.static_api_key_set:
        return StaticAPIKeyAuthAdapter(settings.static_api_key_set)
    return RemoteAuthServiceAdapter(settings.auth_service_url, timeout=settings.auth_service_timeout_seconds)


@lru_cache
def _build_tracer() -> Tracer:
    settings = get_settings()
    provider = TracerProvider(resource=Resource.create({"service.name": "gateway"}))
    exporter = TraceCollectorSpanExporter(
        settings.trace_collector_url, timeout=settings.trace_collector_timeout_seconds
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    # A local, un-registered provider — nothing else in the app calls
    # `opentelemetry.trace.get_tracer()` directly, so there's no need to
    # install this as the process-wide global via `trace.set_tracer_provider`.
    return provider.get_tracer("gateway")


@lru_cache
def _build_usage_sink() -> HttpCostAnalyticsUsageSink:
    settings = get_settings()
    return HttpCostAnalyticsUsageSink(
        settings.cost_analytics_url, timeout=settings.cost_analytics_timeout_seconds
    )


def get_route_chat_use_case() -> RouteChatUseCase:
    return RouteChatUseCase(
        provider_registry=_build_provider_registry(),
        tracing=OtelTracingSink(_build_tracer()),
        usage=_build_usage_sink(),
    )


def get_stream_chat_use_case() -> StreamChatUseCase:
    return StreamChatUseCase(
        provider_registry=_build_provider_registry(),
        tracing=OtelTracingSink(_build_tracer()),
        usage=_build_usage_sink(),
    )


async def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> AuthContext:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    try:
        return await _build_auth_adapter().authenticate(credentials.credentials)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except AuthServiceUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


async def require_chat_scope(auth: Annotated[AuthContext, Depends(require_auth)]) -> AuthContext:
    if not auth.has_scope("chat:write"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="credential lacks chat:write scope")
    return auth


def get_provider_registry() -> ProviderRegistry:
    return _build_provider_registry()


def reset_cached_singletons() -> None:
    """Test-only hook: clears memoized adapters so a test can rebuild them
    against a monkeypatched `Settings`."""
    get_settings.cache_clear()
    _build_provider_registry.cache_clear()
    _build_auth_adapter.cache_clear()
    _build_tracer.cache_clear()
    _build_usage_sink.cache_clear()
