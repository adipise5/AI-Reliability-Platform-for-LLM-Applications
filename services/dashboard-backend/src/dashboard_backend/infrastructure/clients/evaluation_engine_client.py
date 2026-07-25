"""HTTP client for the Evaluation Engine — implements `EvalRunReader` by
forwarding the caller's own bearer credential (the same credential-
forwarding pattern used everywhere else in this project)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import httpx

from dashboard_backend.domain.entities import RemoteEvalRun, RemoteRunItemResult, RemoteScore
from dashboard_backend.domain.errors import RunNotFoundError, UpstreamServiceError


class HttpEvalRunReader:
    def __init__(self, base_url: str, *, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def list_runs(self, credential: str) -> list[RemoteEvalRun]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/runs",
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("evaluation-engine", str(exc)) from exc

        if response.status_code != 200:
            raise UpstreamServiceError("evaluation-engine", f"GET /runs returned {response.status_code}")
        return [_parse_run(item) for item in response.json()]

    async def get_run(
        self, credential: str, run_id: UUID
    ) -> tuple[RemoteEvalRun, tuple[RemoteRunItemResult, ...]]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/runs/{run_id}",
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("evaluation-engine", str(exc)) from exc

        if response.status_code == 404:
            raise RunNotFoundError(run_id)
        if response.status_code != 200:
            raise UpstreamServiceError(
                "evaluation-engine", f"GET /runs/{run_id} returned {response.status_code}"
            )

        payload = response.json()
        run = _parse_run(payload["run"])
        items = tuple(_parse_item(item) for item in payload["items"])
        return run, items


def _parse_run(payload: dict[str, Any]) -> RemoteEvalRun:
    return RemoteEvalRun(
        id=UUID(str(payload["id"])),
        prompt_id=UUID(str(payload["prompt_id"])),
        prompt_version_id=UUID(str(payload["prompt_version_id"])),
        dataset_id=UUID(str(payload["dataset_id"])),
        dataset_version=payload["dataset_version"],
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


def _parse_item(payload: dict[str, Any]) -> RemoteRunItemResult:
    return RemoteRunItemResult(
        id=UUID(str(payload["id"])),
        dataset_item_id=UUID(str(payload["dataset_item_id"])),
        output=str(payload["output"]),
        latency_ms=float(payload["latency_ms"]),
        scores=tuple(
            RemoteScore(scorer_name=str(s["scorer_name"]), value=float(s["value"]))
            for s in payload["scores"]
        ),
    )
