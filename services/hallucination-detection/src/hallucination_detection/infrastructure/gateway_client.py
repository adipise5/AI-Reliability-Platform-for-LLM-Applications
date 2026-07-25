"""A minimal Gateway client — just enough to send one prompt and get text
back. Unlike the Evaluation Engine's `HttpGatewayClient`, this service has
no use for token counts or latency, so it doesn't parse them."""

from __future__ import annotations

import httpx

from hallucination_detection.domain.errors import UpstreamServiceError


class HttpGatewayClient:
    def __init__(self, base_url: str, *, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def complete(self, credential: str, *, model: str, prompt: str) -> str:
        try:
            response = await self._client.post(
                "/api/v1/chat",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                },
                headers={"Authorization": f"Bearer {credential}"},
            )
        except httpx.TransportError as exc:
            raise UpstreamServiceError(str(exc)) from exc

        if response.status_code >= 400:
            raise UpstreamServiceError(f"{response.status_code}: {response.text}")

        content: str = response.json()["content"]
        return content
