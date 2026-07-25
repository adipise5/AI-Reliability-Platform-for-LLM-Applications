"""Ports: interfaces the domain/application layers depend on.

Infrastructure provides concrete adapters implementing these Protocols.
Using ``typing.Protocol`` (structural typing) rather than ABCs keeps test
fakes lightweight — a fake only needs matching method signatures, not
inheritance from a production base class.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from gateway.domain.entities import AuthContext, ChatChunk, ChatRequest, ChatResponse, Provider


class LLMProviderPort(Protocol):
    """A single upstream model provider (Anthropic, OpenAI, Gemini, Ollama)."""

    @property
    def provider(self) -> Provider: ...

    async def complete(self, request: ChatRequest) -> ChatResponse: ...

    def stream(self, request: ChatRequest) -> AsyncIterator[ChatChunk]: ...


class AuthPort(Protocol):
    """Authenticates an inbound request credential. See ADR-0003."""

    async def authenticate(self, credential: str) -> AuthContext: ...


class ProviderRegistry(Protocol):
    """Resolves a caller-facing model string to the provider adapter that
    serves it. Kept out of the use case itself so the model-to-provider
    mapping (a piece of deployment configuration) can change without
    touching application logic."""

    def resolve(self, model: str) -> LLMProviderPort: ...


class TracingSink(Protocol):
    """Where the gateway emits request spans. Backed by the Trace Collector
    from Week 5 onward; a no-op adapter is used until then."""

    async def emit_span(
        self,
        *,
        name: str,
        status: str,
        duration_ms: float,
        attributes: dict[str, str | int | float | bool],
    ) -> None: ...


class UsageSink(Protocol):
    """Where the gateway emits billable usage events. Backed by Cost
    Analytics as of Week 9 — see ADR-0006 for `org_id`."""

    async def emit_usage(
        self,
        *,
        org_id: str,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None: ...
