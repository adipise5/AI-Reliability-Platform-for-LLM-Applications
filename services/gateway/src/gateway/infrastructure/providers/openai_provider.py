"""OpenAI (GPT) adapter, implemented against the official SDK."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator

import openai

from gateway.domain.entities import ChatChunk, ChatRequest, ChatResponse, Provider, Usage
from gateway.domain.errors import ProviderRequestError


class OpenAIProvider:
    provider = Provider.OPENAI

    def __init__(self, api_key: str, *, base_url: str | None = None, timeout: float = 60.0) -> None:
        self._client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    async def complete(self, request: ChatRequest) -> ChatResponse:
        # Plain dicts, not the SDK's ChatCompletion*MessageParam TypedDict
        # union: that union narrows "role" to a Literal, which a
        # runtime-built list can't satisfy statically (see the two
        # `type: ignore[arg-type]` call sites below).
        messages = [{"role": m.role.value, "content": m.content} for m in request.messages]
        started = time.perf_counter()
        try:
            response = await self._client.chat.completions.create(
                model=request.model,
                messages=messages,  # type: ignore[arg-type]
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
        except openai.APIError as exc:
            raise self._wrap(exc) from exc

        latency_ms = (time.perf_counter() - started) * 1000
        choice = response.choices[0]
        usage = response.usage
        return ChatResponse(
            provider=Provider.OPENAI,
            model=response.model,
            content=choice.message.content or "",
            finish_reason=choice.finish_reason or "unknown",
            usage=Usage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
            ),
            latency_ms=latency_ms,
        )

    async def stream(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        messages = [{"role": m.role.value, "content": m.content} for m in request.messages]
        try:
            # The dict-typed `messages` above also makes mypy give up on
            # overload resolution for this call entirely (it can't narrow to
            # the `stream=True` overload once the messages arg mismatches).
            stream = await self._client.chat.completions.create(  # type: ignore[call-overload]
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
                stream_options={"include_usage": True},
            )
            async for event in stream:
                if not event.choices:
                    # Final usage-only chunk when stream_options.include_usage is set.
                    if event.usage:
                        yield ChatChunk(
                            delta="",
                            finish_reason="stop",
                            usage=Usage(
                                prompt_tokens=event.usage.prompt_tokens,
                                completion_tokens=event.usage.completion_tokens,
                            ),
                        )
                    continue
                choice = event.choices[0]
                delta = choice.delta.content or ""
                yield ChatChunk(delta=delta, finish_reason=choice.finish_reason)
        except openai.APIError as exc:
            raise self._wrap(exc) from exc

    @staticmethod
    def _wrap(exc: openai.APIError) -> ProviderRequestError:
        retryable = isinstance(exc, openai.APIConnectionError | openai.RateLimitError)
        return ProviderRequestError("openai", str(exc), retryable=retryable)
