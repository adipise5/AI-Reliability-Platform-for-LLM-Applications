"""Ollama adapter — talks to a local Ollama daemon's REST API.

This is the "local model" provider: no API key, no network egress, and the
catch-all target for any model name that doesn't match a hosted vendor's
prefix (see provider_registry.py).
"""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from gateway.domain.entities import ChatChunk, ChatRequest, ChatResponse, Provider, Usage
from gateway.domain.errors import ProviderRequestError

_RETRYABLE_STATUSES = {408, 409, 429, 500, 502, 503, 504}


class OllamaProvider:
    provider = Provider.OLLAMA

    def __init__(self, base_url: str, *, timeout: float = 120.0) -> None:
        # Local generation can be slow on CPU-only hosts; default timeout is
        # generous relative to the hosted-vendor adapters.
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def complete(self, request: ChatRequest) -> ChatResponse:
        started = time.perf_counter()
        try:
            response = await self._client.post("/api/chat", json=self._build_body(request, stream=False))
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise self._wrap(exc, exc.response.status_code) from exc
        except httpx.TransportError as exc:
            raise ProviderRequestError("ollama", str(exc), retryable=True) from exc

        latency_ms = (time.perf_counter() - started) * 1000
        payload = response.json()
        return ChatResponse(
            provider=Provider.OLLAMA,
            model=payload.get("model", request.model),
            content=payload.get("message", {}).get("content", ""),
            finish_reason="stop" if payload.get("done") else "unknown",
            usage=Usage(
                prompt_tokens=payload.get("prompt_eval_count", 0),
                completion_tokens=payload.get("eval_count", 0),
            ),
            latency_ms=latency_ms,
        )

    async def stream(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        try:
            async with self._client.stream(
                "POST", "/api/chat", json=self._build_body(request, stream=True)
            ) as response:
                if response.status_code >= 400:
                    await response.aread()
                    raise self._wrap(
                        httpx.HTTPStatusError("stream error", request=response.request, response=response),
                        response.status_code,
                    )
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    payload = json.loads(line)
                    content = payload.get("message", {}).get("content", "")
                    if payload.get("done"):
                        yield ChatChunk(
                            delta=content,
                            finish_reason="stop",
                            usage=Usage(
                                prompt_tokens=payload.get("prompt_eval_count", 0),
                                completion_tokens=payload.get("eval_count", 0),
                            ),
                        )
                    else:
                        yield ChatChunk(delta=content)
        except httpx.TransportError as exc:
            raise ProviderRequestError("ollama", str(exc), retryable=True) from exc

    @staticmethod
    def _wrap(exc: Exception, status_code: int) -> ProviderRequestError:
        return ProviderRequestError("ollama", str(exc), retryable=status_code in _RETRYABLE_STATUSES)

    @staticmethod
    def _build_body(request: ChatRequest, *, stream: bool) -> dict[str, Any]:
        return {
            "model": request.model,
            "messages": [{"role": m.role.value, "content": m.content} for m in request.messages],
            "stream": stream,
            "options": {
                "temperature": request.temperature,
                **({"num_predict": request.max_tokens} if request.max_tokens is not None else {}),
            },
        }
