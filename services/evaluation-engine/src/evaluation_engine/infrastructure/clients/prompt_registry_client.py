from __future__ import annotations

from uuid import UUID

import httpx

from evaluation_engine.domain.entities import RemotePromptVersion
from evaluation_engine.domain.errors import UpstreamServiceError
from evaluation_engine.infrastructure.clients.errors import raise_for_upstream_status

_SERVICE = "prompt-registry"


class HttpPromptRegistryClient:
    def __init__(self, base_url: str, *, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def get_version(
        self, credential: str, *, prompt_id: UUID, version_id: UUID
    ) -> RemotePromptVersion:
        try:
            response = await self._client.get(
                f"/api/v1/prompts/{prompt_id}/versions/{version_id}",
                headers={"Authorization": f"Bearer {credential}"},
            )
        except httpx.TransportError as exc:
            raise UpstreamServiceError(_SERVICE, str(exc)) from exc

        raise_for_upstream_status(response, service=_SERVICE)
        payload = response.json()
        return RemotePromptVersion(
            id=UUID(payload["id"]),
            template=payload["template"],
            variables_schema=payload["variables_schema"],
        )
