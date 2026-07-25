from __future__ import annotations

from uuid import UUID

import httpx

from evaluation_engine.domain.entities import RemoteDatasetItem
from evaluation_engine.domain.errors import UpstreamServiceError
from evaluation_engine.infrastructure.clients.errors import raise_for_upstream_status

_SERVICE = "dataset-management"


class HttpDatasetClient:
    def __init__(self, base_url: str, *, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def get_items(
        self, credential: str, *, dataset_id: UUID, version: int | None
    ) -> tuple[int, list[RemoteDatasetItem]]:
        headers = {"Authorization": f"Bearer {credential}"}
        resolved_version = version
        if resolved_version is None:
            resolved_version = await self._resolve_current_version(dataset_id, headers)

        try:
            response = await self._client.get(
                f"/api/v1/datasets/{dataset_id}/items",
                params={"version": resolved_version},
                headers=headers,
            )
        except httpx.TransportError as exc:
            raise UpstreamServiceError(_SERVICE, str(exc)) from exc

        raise_for_upstream_status(response, service=_SERVICE)
        items = [
            RemoteDatasetItem(
                id=UUID(item["id"]),
                input=item["input"],
                expected_output=item["expected_output"],
            )
            for item in response.json()
        ]
        return resolved_version, items

    async def _resolve_current_version(self, dataset_id: UUID, headers: dict[str, str]) -> int:
        try:
            response = await self._client.get(f"/api/v1/datasets/{dataset_id}", headers=headers)
        except httpx.TransportError as exc:
            raise UpstreamServiceError(_SERVICE, str(exc)) from exc

        raise_for_upstream_status(response, service=_SERVICE)
        version: int = response.json()["current_version"]
        return version
