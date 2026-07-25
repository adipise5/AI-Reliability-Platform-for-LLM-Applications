"""Use case: route a single (non-streaming) chat request to a provider.

This is the only place that decides "what happens on a /chat call" — auth
context is assumed already resolved by the caller (the API layer), so this
use case is testable with fakes and has no HTTP concerns at all.
"""

from __future__ import annotations

import time

from gateway.domain.entities import ChatRequest, ChatResponse
from gateway.domain.errors import ProviderRequestError
from gateway.domain.ports import ProviderRegistry, TracingSink, UsageSink


class RouteChatUseCase:
    def __init__(
        self,
        provider_registry: ProviderRegistry,
        tracing: TracingSink,
        usage: UsageSink,
    ) -> None:
        self._registry = provider_registry
        self._tracing = tracing
        self._usage = usage

    async def execute(self, request: ChatRequest, *, org_id: str) -> ChatResponse:
        provider = self._registry.resolve(request.model)
        started = time.perf_counter()
        status = "ok"
        try:
            response = await provider.complete(request)
        except ProviderRequestError:
            status = "error"
            raise
        finally:
            duration_ms = (time.perf_counter() - started) * 1000
            await self._tracing.emit_span(
                name="gateway.chat",
                status=status,
                duration_ms=duration_ms,
                attributes={"model": request.model, "stream": False, "org_id": org_id},
            )

        await self._usage.emit_usage(
            org_id=org_id,
            provider=response.provider.value,
            model=response.model,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
        )
        return response
