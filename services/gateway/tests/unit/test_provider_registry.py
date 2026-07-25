from __future__ import annotations

import pytest

from gateway.domain.entities import Provider
from gateway.domain.errors import UnsupportedModelError
from gateway.infrastructure.provider_registry import ModelPrefixProviderRegistry


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("claude-sonnet-5", Provider.ANTHROPIC),
        ("claude-opus-4-8", Provider.ANTHROPIC),
        ("gpt-5", Provider.OPENAI),
        ("o1-preview", Provider.OPENAI),
        ("o3-mini", Provider.OPENAI),
        ("gemini-2.5-pro", Provider.GEMINI),
        ("llama3.1", Provider.OLLAMA),
        ("mistral", Provider.OLLAMA),
        ("CLAUDE-SONNET-5", Provider.ANTHROPIC),  # matching is case-insensitive
    ],
)
def test_resolve_matches_expected_provider(model, expected):
    marker = object()
    registry = ModelPrefixProviderRegistry({expected: marker})

    assert registry.resolve(model) is marker


def test_resolve_raises_when_matched_provider_not_registered():
    registry = ModelPrefixProviderRegistry({Provider.OLLAMA: object()})

    with pytest.raises(UnsupportedModelError) as exc_info:
        registry.resolve("gpt-5")

    assert exc_info.value.model == "gpt-5"
