from __future__ import annotations

import httpx

from evaluation_engine.domain.errors import UpstreamServiceError
from evaluation_engine.infrastructure.clients.errors import raise_for_upstream_status

_SERVICE = "hallucination-detection"


class HttpHallucinationDetectionClient:
    def __init__(self, base_url: str, *, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def check_faithfulness(
        self, credential: str, *, model: str, response: str, context: str
    ) -> tuple[float, int]:
        try:
            http_response = await self._client.post(
                "/api/v1/faithfulness-checks",
                json={"model": model, "response": response, "context": context},
                headers={"Authorization": f"Bearer {credential}"},
            )
        except httpx.TransportError as exc:
            raise UpstreamServiceError(_SERVICE, str(exc)) from exc

        raise_for_upstream_status(http_response, service=_SERVICE)
        payload = http_response.json()
        return payload["faithfulness_score"], len(payload["claims"])
