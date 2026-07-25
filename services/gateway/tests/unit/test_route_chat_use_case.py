from __future__ import annotations

import pytest

from gateway.application.route_chat import RouteChatUseCase
from gateway.domain.errors import ProviderRequestError
from tests.unit.conftest import FakeProvider, FakeProviderRegistry, RecordingTracingSink, RecordingUsageSink


async def test_execute_returns_provider_response_and_records_usage(sample_request, sample_response):
    provider = FakeProvider(response=sample_response)
    tracing = RecordingTracingSink()
    usage = RecordingUsageSink()
    use_case = RouteChatUseCase(FakeProviderRegistry(provider), tracing, usage)

    result = await use_case.execute(sample_request, org_id="org-1")

    assert result is sample_response
    assert provider.complete_calls == [sample_request]
    assert usage.events == [
        {
            "org_id": "org-1",
            "provider": "anthropic",
            "model": "claude-sonnet-5",
            "prompt_tokens": 5,
            "completion_tokens": 3,
        }
    ]


async def test_execute_emits_ok_span_on_success(sample_request, sample_response):
    tracing = RecordingTracingSink()
    use_case = RouteChatUseCase(
        FakeProviderRegistry(FakeProvider(response=sample_response)), tracing, RecordingUsageSink()
    )

    await use_case.execute(sample_request, org_id="org-1")

    assert len(tracing.spans) == 1
    assert tracing.spans[0]["status"] == "ok"
    assert tracing.spans[0]["attributes"]["stream"] is False
    assert tracing.spans[0]["attributes"]["org_id"] == "org-1"


async def test_execute_emits_error_span_and_reraises_on_provider_failure(sample_request):
    error = ProviderRequestError("anthropic", "boom", retryable=True)
    tracing = RecordingTracingSink()
    usage = RecordingUsageSink()
    use_case = RouteChatUseCase(FakeProviderRegistry(FakeProvider(error=error)), tracing, usage)

    with pytest.raises(ProviderRequestError):
        await use_case.execute(sample_request, org_id="org-1")

    assert tracing.spans[0]["status"] == "error"
    # A failed call must never be billed.
    assert usage.events == []
