from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from gateway.api import deps
from gateway.api.main import create_app
from gateway.domain.entities import AuthContext, ChatChunk, ChatRequest, ChatResponse, Provider, Usage


class FakeRouteChatUseCase:
    def __init__(self, response: ChatResponse | None = None, error: Exception | None = None) -> None:
        self._response = response
        self._error = error

    async def execute(self, request: ChatRequest, *, org_id: str) -> ChatResponse:
        if self._error:
            raise self._error
        assert self._response is not None
        return self._response


class FakeStreamChatUseCase:
    def __init__(self, chunks: list[ChatChunk] | None = None) -> None:
        self._chunks = chunks or []

    async def execute(self, request: ChatRequest, *, org_id: str) -> AsyncIterator[ChatChunk]:
        for chunk in self._chunks:
            yield chunk


class FakeRegistry:
    def resolve(self, model: str):
        return object()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def authorized_client(app):
    app.dependency_overrides[deps.require_chat_scope] = lambda: AuthContext(
        subject="test-user", org_id="org-1", scopes=frozenset({"chat:write"})
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_chat_response() -> ChatResponse:
    return ChatResponse(
        provider=Provider.ANTHROPIC,
        model="claude-sonnet-5",
        content="hello!",
        finish_reason="end_turn",
        usage=Usage(prompt_tokens=5, completion_tokens=3),
        latency_ms=9.5,
    )
