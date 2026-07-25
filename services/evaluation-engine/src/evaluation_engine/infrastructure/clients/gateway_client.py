from __future__ import annotations

import httpx

from evaluation_engine.domain.entities import RemoteCompletion
from evaluation_engine.domain.errors import UpstreamServiceError
from evaluation_engine.infrastructure.clients.errors import raise_for_upstream_status

_SERVICE = "gateway"


class HttpGatewayClient:
    def __init__(self, base_url: str, *, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def complete(
        self,
        credential: str,
        *,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int | None,
    ) -> RemoteCompletion:
        body: dict[str, object] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        if max_tokens is not None:
            body["max_tokens"] = max_tokens

        try:
            response = await self._client.post(
                "/api/v1/chat",
                json=body,
                headers={"Authorization": f"Bearer {credential}"},
            )
        except httpx.TransportError as exc:
            raise UpstreamServiceError(_SERVICE, str(exc)) from exc

        raise_for_upstream_status(response, service=_SERVICE)
        payload = response.json()
        usage = payload["usage"]
        return RemoteCompletion(
            content=payload["content"],
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            latency_ms=payload["latency_ms"],
        )
