"""Use case: stream a chat completion from a provider chunk by chunk."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator

from gateway.domain.entities import ChatChunk, ChatRequest
from gateway.domain.errors import ProviderRequestError
from gateway.domain.ports import ProviderRegistry, TracingSink, UsageSink


class StreamChatUseCase:
    def __init__(
        self,
        provider_registry: ProviderRegistry,
        tracing: TracingSink,
        usage: UsageSink,
    ) -> None:
        self._registry = provider_registry
        self._tracing = tracing
        self._usage = usage

    async def execute(self, request: ChatRequest, *, org_id: str) -> AsyncIterator[ChatChunk]:
        provider = self._registry.resolve(request.model)
        started = time.perf_counter()
        status = "ok"
        try:
            async for chunk in provider.stream(request):
                if chunk.usage is not None:
                    await self._usage.emit_usage(
                        org_id=org_id,
                        provider=provider.provider.value,
                        model=request.model,
                        prompt_tokens=chunk.usage.prompt_tokens,
                        completion_tokens=chunk.usage.completion_tokens,
                    )
                yield chunk
        except ProviderRequestError:
            status = "error"
            raise
        finally:
            duration_ms = (time.perf_counter() - started) * 1000
            await self._tracing.emit_span(
                name="gateway.chat",
                status=status,
                duration_ms=duration_ms,
                attributes={"model": request.model, "stream": True, "org_id": org_id},
            )
