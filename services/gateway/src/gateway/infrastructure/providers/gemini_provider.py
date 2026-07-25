"""Gemini adapter, implemented directly against the Generative Language REST
API rather than a vendor SDK — keeps the gateway's dependency surface to
one HTTP client (httpx) for the two providers without a mature async SDK.
"""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from gateway.domain.entities import ChatChunk, ChatRequest, ChatResponse, Provider, Role, Usage
from gateway.domain.errors import ProviderRequestError

_RETRYABLE_STATUSES = {408, 409, 429, 500, 502, 503, 504}


class GeminiProvider:
    provider = Provider.GEMINI

    def __init__(self, api_key: str, *, base_url: str, timeout: float = 60.0) -> None:
        self._api_key = api_key
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def complete(self, request: ChatRequest) -> ChatResponse:
        body = self._build_body(request)
        started = time.perf_counter()
        try:
            response = await self._client.post(
                f"/v1beta/models/{request.model}:generateContent",
                params={"key": self._api_key},
                json=body,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise self._wrap(exc, exc.response.status_code) from exc
        except httpx.TransportError as exc:
            raise ProviderRequestError("gemini", str(exc), retryable=True) from exc

        latency_ms = (time.perf_counter() - started) * 1000
        payload = response.json()
        candidate = payload["candidates"][0]
        text = "".join(part.get("text", "") for part in candidate["content"]["parts"])
        usage_meta = payload.get("usageMetadata", {})
        return ChatResponse(
            provider=Provider.GEMINI,
            model=request.model,
            content=text,
            finish_reason=candidate.get("finishReason", "unknown").lower(),
            usage=Usage(
                prompt_tokens=usage_meta.get("promptTokenCount", 0),
                completion_tokens=usage_meta.get("candidatesTokenCount", 0),
            ),
            latency_ms=latency_ms,
        )

    async def stream(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        body = self._build_body(request)
        try:
            async with self._client.stream(
                "POST",
                f"/v1beta/models/{request.model}:streamGenerateContent",
                params={"key": self._api_key, "alt": "sse"},
                json=body,
            ) as response:
                await self._raise_for_stream_status(response)
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = json.loads(line.removeprefix("data: "))
                    candidate = payload["candidates"][0]
                    parts = candidate.get("content", {}).get("parts", [])
                    text = "".join(part.get("text", "") for part in parts)
                    finish_reason = candidate.get("finishReason")
                    usage_meta = payload.get("usageMetadata")
                    usage = (
                        Usage(
                            prompt_tokens=usage_meta.get("promptTokenCount", 0),
                            completion_tokens=usage_meta.get("candidatesTokenCount", 0),
                        )
                        if usage_meta and finish_reason
                        else None
                    )
                    yield ChatChunk(
                        delta=text,
                        finish_reason=finish_reason.lower() if finish_reason else None,
                        usage=usage,
                    )
        except httpx.TransportError as exc:
            raise ProviderRequestError("gemini", str(exc), retryable=True) from exc

    async def _raise_for_stream_status(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            await response.aread()
            raise self._wrap(
                httpx.HTTPStatusError("stream error", request=response.request, response=response),
                response.status_code,
            )

    @staticmethod
    def _wrap(exc: Exception, status_code: int) -> ProviderRequestError:
        return ProviderRequestError("gemini", str(exc), retryable=status_code in _RETRYABLE_STATUSES)

    @staticmethod
    def _build_body(request: ChatRequest) -> dict[str, Any]:
        system_parts = [m.content for m in request.messages if m.role == Role.SYSTEM]
        contents = [
            {"role": _to_gemini_role(m.role), "parts": [{"text": m.content}]}
            for m in request.messages
            if m.role != Role.SYSTEM
        ]
        body: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": request.temperature},
        }
        if request.max_tokens is not None:
            body["generationConfig"]["maxOutputTokens"] = request.max_tokens
        if system_parts:
            body["systemInstruction"] = {"parts": [{"text": "\n".join(system_parts)}]}
        return body


def _to_gemini_role(role: Role) -> str:
    # Gemini uses "model" where every other provider says "assistant".
    return "model" if role == Role.ASSISTANT else "user"
