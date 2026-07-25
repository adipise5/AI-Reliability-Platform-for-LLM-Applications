"""HTTP client for Regression Detection — implements `GateDecisionReader`
by forwarding the caller's own bearer credential (same credential-
forwarding pattern as every other cross-service reader in this project).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from github_integration.domain.entities import RemoteGateDecision
from github_integration.domain.errors import UpstreamServiceError


class HttpGateDecisionReader:
    def __init__(self, base_url: str, *, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def get_gate_decision(self, credential: str, run_id: UUID) -> RemoteGateDecision:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/gate-decisions/{run_id}",
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("regression-detection", str(exc)) from exc

        if response.status_code != 200:
            raise UpstreamServiceError(
                "regression-detection",
                f"GET /gate-decisions/{run_id} returned {response.status_code}",
            )
        return _parse_gate_decision(response.json())


def _parse_gate_decision(payload: dict[str, Any]) -> RemoteGateDecision:
    return RemoteGateDecision(
        run_id=UUID(str(payload["run_id"])),
        verdict=str(payload["verdict"]),
        observed_score=float(payload["observed_score"]),
        baseline_mean=float(payload["baseline_mean"]),
        baseline_stddev=float(payload["baseline_stddev"]),
    )
