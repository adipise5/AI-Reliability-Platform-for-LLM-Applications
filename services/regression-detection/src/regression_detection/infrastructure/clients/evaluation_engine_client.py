"""HTTP client for the Evaluation Engine — implements `EvalRunReader` by
forwarding the caller's own bearer credential (see ADR-0005/credential
forwarding precedent in Experiment Tracking, Week 8)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from regression_detection.domain.entities import RemoteEvalRun
from regression_detection.domain.errors import UpstreamServiceError


class HttpEvalRunReader:
    def __init__(self, base_url: str, *, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def get_run(self, credential: str, run_id: UUID) -> RemoteEvalRun:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/runs/{run_id}",
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("evaluation-engine", str(exc)) from exc

        if response.status_code != 200:
            raise UpstreamServiceError(
                "evaluation-engine", f"GET /runs/{run_id} returned {response.status_code}"
            )
        return _parse_run(response.json()["run"])

    async def list_runs(self, credential: str, *, prompt_id: UUID) -> list[RemoteEvalRun]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/runs",
                    params={"prompt_id": str(prompt_id)},
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("evaluation-engine", str(exc)) from exc

        if response.status_code != 200:
            raise UpstreamServiceError(
                "evaluation-engine", f"GET /runs returned {response.status_code}"
            )
        return [_parse_run(item) for item in response.json()]


def _parse_run(payload: dict[str, Any]) -> RemoteEvalRun:
    return RemoteEvalRun(
        id=UUID(str(payload["id"])),
        prompt_id=UUID(str(payload["prompt_id"])),
        status=str(payload["status"]),
        aggregate_score=payload["aggregate_score"],
    )
