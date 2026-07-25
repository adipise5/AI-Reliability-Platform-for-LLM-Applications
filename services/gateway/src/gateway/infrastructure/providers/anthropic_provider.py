"""Anthropic (Claude) adapter, implemented against the official SDK."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator

import anthropic

from gateway.domain.entities import ChatChunk, ChatMessage, ChatRequest, ChatResponse, Provider, Role, Usage
from gateway.domain.errors import ProviderRequestError


class AnthropicProvider:
    provider = Provider.ANTHROPIC

    def __init__(self, api_key: str, *, base_url: str | None = None, timeout: float = 60.0) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key, base_url=base_url, timeout=timeout)

    async def complete(self, request: ChatRequest) -> ChatResponse:
        system, messages = self._split_system(request.messages)
        started = time.perf_counter()
        try:
            response = await self._client.messages.create(
                model=request.model,
                system=system or anthropic.NOT_GIVEN,  # type: ignore[arg-type]
                messages=messages,  # type: ignore[arg-type]
                temperature=request.temperature,
                max_tokens=request.max_tokens or 1024,
            )
        except anthropic.APIError as exc:
            raise self._wrap(exc) from exc

        latency_ms = (time.perf_counter() - started) * 1000
        text = "".join(block.text for block in response.content if block.type == "text")
        return ChatResponse(
            provider=Provider.ANTHROPIC,
            model=response.model,
            content=text,
            finish_reason=response.stop_reason or "unknown",
            usage=Usage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
            ),
            latency_ms=latency_ms,
        )

    async def stream(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        system, messages = self._split_system(request.messages)
        try:
            async with self._client.messages.stream(
                model=request.model,
                system=system or anthropic.NOT_GIVEN,  # type: ignore[arg-type]
                messages=messages,  # type: ignore[arg-type]
                temperature=request.temperature,
                max_tokens=request.max_tokens or 1024,
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta" and event.delta.type == "text_delta":
                        yield ChatChunk(delta=event.delta.text)
                final = await stream.get_final_message()
                yield ChatChunk(
                    delta="",
                    finish_reason=final.stop_reason or "unknown",
                    usage=Usage(
                        prompt_tokens=final.usage.input_tokens,
                        completion_tokens=final.usage.output_tokens,
                    ),
                )
        except anthropic.APIError as exc:
            raise self._wrap(exc) from exc

    @staticmethod
    def _wrap(exc: anthropic.APIError) -> ProviderRequestError:
        retryable = isinstance(exc, anthropic.APIConnectionError | anthropic.RateLimitError)
        return ProviderRequestError("anthropic", str(exc), retryable=retryable)

    @staticmethod
    def _split_system(messages: tuple[ChatMessage, ...]) -> tuple[str | None, list[dict[str, str]]]:
        # Plain dicts, not anthropic.types.MessageParam: the SDK's TypedDicts
        # narrow "role" to a Literal, which a runtime-filtered list
        # comprehension can't satisfy statically. The two call sites above
        # are `type: ignore[arg-type]`'d for the same reason.
        system_parts = [m.content for m in messages if m.role == Role.SYSTEM]
        system = "\n".join(system_parts) or None
        chat = [{"role": m.role.value, "content": m.content} for m in messages if m.role != Role.SYSTEM]
        return system, chat
