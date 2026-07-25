"""HTTP client for Regression Detection — implements `RegressionReader`.
`get_baseline`/`get_gate_decision` forward the caller's bearer credential
and return `None` on a 404 rather than raising — see `domain/ports.py`'s
module docstring for why. `get_latency_anomaly` sends no credential at
all, since that endpoint is itself unauthenticated upstream.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from dashboard_backend.domain.entities import RemoteBaseline, RemoteGateDecision, RemoteLatencyAnomaly
from dashboard_backend.domain.errors import UpstreamServiceError


class HttpRegressionReader:
    def __init__(self, base_url: str, *, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def get_baseline(self, credential: str, prompt_id: UUID) -> RemoteBaseline | None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/baselines/{prompt_id}",
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("regression-detection", str(exc)) from exc

        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise UpstreamServiceError(
                "regression-detection", f"GET /baselines/{prompt_id} returned {response.status_code}"
            )
        payload = response.json()
        return RemoteBaseline(
            prompt_id=UUID(str(payload["prompt_id"])),
            mean_score=float(payload["mean_score"]),
            stddev_score=float(payload["stddev_score"]),
            sample_size=int(payload["sample_size"]),
        )

    async def get_gate_decision(self, credential: str, run_id: UUID) -> RemoteGateDecision | None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/gate-decisions/{run_id}",
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("regression-detection", str(exc)) from exc

        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise UpstreamServiceError(
                "regression-detection",
                f"GET /gate-decisions/{run_id} returned {response.status_code}",
            )
        return _parse_gate_decision(response.json())

    async def get_latency_anomaly(self) -> RemoteLatencyAnomaly:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(f"{self._base_url}/api/v1/latency-anomaly")
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("regression-detection", str(exc)) from exc

        if response.status_code != 200:
            raise UpstreamServiceError(
                "regression-detection", f"GET /latency-anomaly returned {response.status_code}"
            )
        payload = response.json()
        return RemoteLatencyAnomaly(
            sample_count=int(payload["sample_count"]),
            recent_mean_ms=payload["recent_mean_ms"],
            baseline_mean_ms=payload["baseline_mean_ms"],
            baseline_stddev_ms=payload["baseline_stddev_ms"],
            is_anomalous=bool(payload["is_anomalous"]),
            insufficient_data=bool(payload["insufficient_data"]),
        )


def _parse_gate_decision(payload: dict[str, Any]) -> RemoteGateDecision:
    return RemoteGateDecision(
        run_id=UUID(str(payload["run_id"])),
        verdict=str(payload["verdict"]),
        observed_score=float(payload["observed_score"]),
        baseline_mean=float(payload["baseline_mean"]),
        baseline_stddev=float(payload["baseline_stddev"]),
    )
