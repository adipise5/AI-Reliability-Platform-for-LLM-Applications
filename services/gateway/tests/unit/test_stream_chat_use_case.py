from __future__ import annotations

import pytest

from gateway.application.stream_chat import StreamChatUseCase
from gateway.domain.entities import ChatChunk, Usage
from gateway.domain.errors import ProviderRequestError
from tests.unit.conftest import FakeProvider, FakeProviderRegistry, RecordingTracingSink, RecordingUsageSink


async def test_execute_yields_all_chunks_and_records_usage_on_final_chunk(sample_request):
    chunks = [
        ChatChunk(delta="hel"),
        ChatChunk(delta="lo"),
        ChatChunk(delta="", finish_reason="end_turn", usage=Usage(prompt_tokens=5, completion_tokens=2)),
    ]
    tracing = RecordingTracingSink()
    usage = RecordingUsageSink()
    use_case = StreamChatUseCase(FakeProviderRegistry(FakeProvider(chunks=chunks)), tracing, usage)

    collected = [chunk async for chunk in use_case.execute(sample_request, org_id="org-1")]

    assert collected == chunks
    assert usage.events == [
        {
            "org_id": "org-1",
            "provider": "anthropic",
            "model": "claude-sonnet-5",
            "prompt_tokens": 5,
            "completion_tokens": 2,
        }
    ]
    assert tracing.spans[0]["attributes"]["stream"] is True
    assert tracing.spans[0]["attributes"]["org_id"] == "org-1"
    assert tracing.spans[0]["status"] == "ok"


async def test_execute_propagates_provider_error_mid_stream(sample_request):
    error = ProviderRequestError("anthropic", "connection reset", retryable=True)
    tracing = RecordingTracingSink()
    use_case = StreamChatUseCase(
        FakeProviderRegistry(FakeProvider(error=error)), tracing, RecordingUsageSink()
    )

    with pytest.raises(ProviderRequestError):
        async for _ in use_case.execute(sample_request, org_id="org-1"):
            pass

    assert tracing.spans[0]["status"] == "error"
