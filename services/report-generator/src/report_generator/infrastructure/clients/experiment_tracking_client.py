"""HTTP client for Experiment Tracking — implements `ExperimentReader` by
forwarding the caller's own bearer credential (same credential-forwarding
pattern as every other cross-service reader in this project)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import httpx

from report_generator.domain.entities import RemoteExperiment, RemoteExperimentComparison, RemoteRunSummary
from report_generator.domain.errors import UpstreamServiceError


class HttpExperimentReader:
    def __init__(self, base_url: str, *, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def get_comparison(self, credential: str, experiment_id: UUID) -> RemoteExperimentComparison:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/experiments/{experiment_id}/comparison",
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("experiment-tracking", str(exc)) from exc

        if response.status_code != 200:
            raise UpstreamServiceError(
                "experiment-tracking",
                f"GET /experiments/{experiment_id}/comparison returned {response.status_code}",
            )

        payload = response.json()
        return RemoteExperimentComparison(
            experiment=_parse_experiment(payload["experiment"]),
            runs=tuple(_parse_run(item) for item in payload["runs"]),
        )


def _parse_experiment(payload: dict[str, Any]) -> RemoteExperiment:
    return RemoteExperiment(
        id=UUID(str(payload["id"])),
        name=str(payload["name"]),
        description=str(payload["description"]),
        run_ids=tuple(UUID(str(rid)) for rid in payload["run_ids"]),
    )


def _parse_run(payload: dict[str, Any]) -> RemoteRunSummary:
    return RemoteRunSummary(
        id=UUID(str(payload["id"])),
        prompt_id=UUID(str(payload["prompt_id"])),
        model=str(payload["model"]),
        status=str(payload["status"]),
        aggregate_score=payload["aggregate_score"],
        created_at=datetime.fromisoformat(str(payload["created_at"])),
        completed_at=(
            datetime.fromisoformat(str(payload["completed_at"]))
            if payload.get("completed_at") is not None
            else None
        ),
    )
