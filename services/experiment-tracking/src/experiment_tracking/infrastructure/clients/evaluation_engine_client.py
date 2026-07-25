from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import httpx

from experiment_tracking.domain.entities import RemoteEvalRunSummary
from experiment_tracking.domain.errors import RunNotFoundError, UpstreamServiceError

_SERVICE = "evaluation-engine"


class HttpEvalRunReader:
    def __init__(self, base_url: str, *, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def get_run(self, credential: str, run_id: UUID) -> RemoteEvalRunSummary:
        try:
            response = await self._client.get(
                f"/api/v1/runs/{run_id}", headers={"Authorization": f"Bearer {credential}"}
            )
        except httpx.TransportError as exc:
            raise UpstreamServiceError(_SERVICE, str(exc)) from exc

        if response.status_code == 404:
            raise RunNotFoundError(run_id)
        if response.status_code >= 400:
            raise UpstreamServiceError(_SERVICE, f"{response.status_code}: {response.text}")

        return _to_summary(response.json()["run"])

    async def list_runs(
        self, credential: str, *, prompt_id: UUID | None = None, dataset_id: UUID | None = None
    ) -> list[RemoteEvalRunSummary]:
        params: dict[str, str] = {}
        if prompt_id is not None:
            params["prompt_id"] = str(prompt_id)
        if dataset_id is not None:
            params["dataset_id"] = str(dataset_id)

        try:
            response = await self._client.get(
                "/api/v1/runs", params=params, headers={"Authorization": f"Bearer {credential}"}
            )
        except httpx.TransportError as exc:
            raise UpstreamServiceError(_SERVICE, str(exc)) from exc

        if response.status_code >= 400:
            raise UpstreamServiceError(_SERVICE, f"{response.status_code}: {response.text}")

        return [_to_summary(run) for run in response.json()]


def _to_summary(payload: dict[str, Any]) -> RemoteEvalRunSummary:
    completed_at = payload["completed_at"]
    return RemoteEvalRunSummary(
        id=UUID(str(payload["id"])),
        prompt_id=UUID(str(payload["prompt_id"])),
        prompt_version_id=UUID(str(payload["prompt_version_id"])),
        dataset_id=UUID(str(payload["dataset_id"])),
        dataset_version=payload["dataset_version"],
        model=payload["model"],
        status=payload["status"],
        aggregate_score=payload["aggregate_score"],
        created_at=datetime.fromisoformat(payload["created_at"]),
        completed_at=datetime.fromisoformat(completed_at) if completed_at else None,
    )
