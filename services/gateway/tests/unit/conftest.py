from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from gateway.domain.entities import ChatChunk, ChatRequest, ChatResponse, Provider, Usage
from gateway.domain.errors import ProviderRequestError


class FakeProvider:
    """A test double for LLMProviderPort with scripted responses/errors."""

    def __init__(
        self,
        *,
        provider: Provider = Provider.ANTHROPIC,
        response: ChatResponse | None = None,
        chunks: list[ChatChunk] | None = None,
        error: ProviderRequestError | None = None,
    ) -> None:
        self.provider = provider
        self._response = response
        self._chunks = chunks or []
        self._error = error
        self.complete_calls: list[ChatRequest] = []
        self.stream_calls: list[ChatRequest] = []

    async def complete(self, request: ChatRequest) -> ChatResponse:
        self.complete_calls.append(request)
        if self._error:
            raise self._error
        assert self._response is not None
        return self._response

    async def stream(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        self.stream_calls.append(request)
        if self._error:
            raise self._error
        for chunk in self._chunks:
            yield chunk


class FakeProviderRegistry:
    def __init__(self, provider: FakeProvider) -> None:
        self._provider = provider

    def resolve(self, model: str) -> FakeProvider:
        return self._provider


class RecordingTracingSink:
    def __init__(self) -> None:
        self.spans: list[dict] = []

    async def emit_span(self, *, name: str, status: str, duration_ms: float, attributes: dict) -> None:
        self.spans.append(
            {"name": name, "status": status, "duration_ms": duration_ms, "attributes": attributes}
        )


class RecordingUsageSink:
    def __init__(self) -> None:
        self.events: list[dict] = []

    async def emit_usage(
        self, *, org_id: str, provider: str, model: str, prompt_tokens: int, completion_tokens: int
    ) -> None:
        self.events.append(
            {
                "org_id": org_id,
                "provider": provider,
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            }
        )


@pytest.fixture
def sample_request() -> ChatRequest:
    from gateway.domain.entities import ChatMessage, Role

    return ChatRequest(model="claude-sonnet-5", messages=(ChatMessage(role=Role.USER, content="hi"),))


@pytest.fixture
def sample_response() -> ChatResponse:
    return ChatResponse(
        provider=Provider.ANTHROPIC,
        model="claude-sonnet-5",
        content="hello!",
        finish_reason="end_turn",
        usage=Usage(prompt_tokens=5, completion_tokens=3),
        latency_ms=12.3,
    )
