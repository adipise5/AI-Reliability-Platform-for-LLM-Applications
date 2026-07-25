"""HTTP client for Cost Analytics — implements `CostReader` by
forwarding the caller's own bearer credential."""

from __future__ import annotations

from typing import Any

import httpx

from dashboard_backend.domain.entities import RemoteBudgetStatus, RemoteModelUsage, RemoteUsageSummary
from dashboard_backend.domain.errors import UpstreamServiceError


class HttpCostReader:
    def __init__(self, base_url: str, *, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def get_usage_summary(self, credential: str) -> RemoteUsageSummary:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/usage",
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("cost-analytics", str(exc)) from exc

        if response.status_code != 200:
            raise UpstreamServiceError("cost-analytics", f"GET /usage returned {response.status_code}")
        return _parse_usage_summary(response.json())

    async def get_budget_status(self, credential: str) -> RemoteBudgetStatus:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/budget",
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("cost-analytics", str(exc)) from exc

        if response.status_code != 200:
            raise UpstreamServiceError("cost-analytics", f"GET /budget returned {response.status_code}")
        payload = response.json()
        return RemoteBudgetStatus(
            spent_this_month_usd=float(payload["spent_this_month_usd"]),
            limit_usd=payload["limit_usd"],
            remaining_usd=payload["remaining_usd"],
            over_budget=bool(payload["over_budget"]),
        )


def _parse_usage_summary(payload: dict[str, Any]) -> RemoteUsageSummary:
    return RemoteUsageSummary(
        total_cost_usd=float(payload["total_cost_usd"]),
        total_prompt_tokens=int(payload["total_prompt_tokens"]),
        total_completion_tokens=int(payload["total_completion_tokens"]),
        by_model=tuple(
            RemoteModelUsage(
                provider=str(m["provider"]),
                model=str(m["model"]),
                prompt_tokens=int(m["prompt_tokens"]),
                completion_tokens=int(m["completion_tokens"]),
                cost_usd=float(m["cost_usd"]),
            )
            for m in payload["by_model"]
        ),
    )
