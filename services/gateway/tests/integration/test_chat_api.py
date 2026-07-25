from __future__ import annotations

from fastapi.testclient import TestClient

from gateway.api import deps
from gateway.domain.entities import ChatChunk, Usage
from gateway.domain.errors import ProviderRequestError, UnsupportedModelError
from tests.integration.conftest import FakeRegistry, FakeRouteChatUseCase, FakeStreamChatUseCase

PAYLOAD = {"model": "claude-sonnet-5", "messages": [{"role": "user", "content": "hi"}]}


def test_chat_completion_requires_authorization_header(app):
    client = TestClient(app)

    response = client.post("/api/v1/chat", json=PAYLOAD)

    assert response.status_code == 401


def test_chat_completion_returns_normalized_response(app, authorized_client, sample_chat_response):
    app.dependency_overrides[deps.get_route_chat_use_case] = lambda: FakeRouteChatUseCase(
        response=sample_chat_response
    )

    response = authorized_client.post(
        "/api/v1/chat", json=PAYLOAD, headers={"Authorization": "Bearer irrelevant"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "anthropic"
    assert body["content"] == "hello!"
    assert body["usage"] == {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}


def test_chat_completion_maps_unsupported_model_to_400(app, authorized_client):
    app.dependency_overrides[deps.get_route_chat_use_case] = lambda: FakeRouteChatUseCase(
        error=UnsupportedModelError("mystery-model")
    )

    response = authorized_client.post(
        "/api/v1/chat", json=PAYLOAD, headers={"Authorization": "Bearer irrelevant"}
    )

    assert response.status_code == 400
    assert response.json()["type"] == "unsupported_model"


def test_chat_completion_maps_provider_error_to_502(app, authorized_client):
    app.dependency_overrides[deps.get_route_chat_use_case] = lambda: FakeRouteChatUseCase(
        error=ProviderRequestError("anthropic", "upstream rate limited", retryable=True)
    )

    response = authorized_client.post(
        "/api/v1/chat", json=PAYLOAD, headers={"Authorization": "Bearer irrelevant"}
    )

    assert response.status_code == 502
    body = response.json()
    assert body["type"] == "provider_error"
    assert body["retryable"] is True


def test_stream_chat_completion_emits_sse_chunks_terminated_by_done(app, authorized_client):
    chunks = [
        ChatChunk(delta="hel"),
        ChatChunk(delta="lo", finish_reason="end_turn", usage=Usage(prompt_tokens=5, completion_tokens=2)),
    ]
    app.dependency_overrides[deps.get_stream_chat_use_case] = lambda: FakeStreamChatUseCase(chunks=chunks)
    app.dependency_overrides[deps.get_provider_registry] = FakeRegistry

    response = authorized_client.post(
        "/api/v1/chat/stream", json=PAYLOAD, headers={"Authorization": "Bearer irrelevant"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert '"delta":"hel"' in body
    assert '"delta":"lo"' in body
    assert body.strip().endswith("data: [DONE]")
