"""Maps caller-facing model strings to the adapter that serves them."""

from __future__ import annotations

from collections.abc import Mapping

from gateway.domain.entities import Provider
from gateway.domain.errors import UnsupportedModelError
from gateway.domain.ports import LLMProviderPort

# Ordered so the first matching prefix wins. Anything unmatched falls back to
# Ollama — local model names ("llama3.1", "mistral", "phi3", ...) have no
# shared prefix, so "not one of the three hosted vendors" is the practical
# signal that a request is for a local model.
_PREFIX_TO_PROVIDER: tuple[tuple[str, Provider], ...] = (
    ("claude", Provider.ANTHROPIC),
    ("gpt", Provider.OPENAI),
    ("o1", Provider.OPENAI),
    ("o3", Provider.OPENAI),
    ("gemini", Provider.GEMINI),
)


class ModelPrefixProviderRegistry:
    def __init__(self, providers: Mapping[Provider, LLMProviderPort]) -> None:
        self._providers = providers

    def resolve(self, model: str) -> LLMProviderPort:
        target = self._match(model)
        try:
            return self._providers[target]
        except KeyError:
            raise UnsupportedModelError(model) from None

    @staticmethod
    def _match(model: str) -> Provider:
        lowered = model.lower()
        for prefix, provider in _PREFIX_TO_PROVIDER:
            if lowered.startswith(prefix):
                return provider
        return Provider.OLLAMA
