"""HTTP client for the Report Generator — implements `ReportReader` by
forwarding the caller's own bearer credential."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import httpx

from dashboard_backend.domain.entities import RemoteReport
from dashboard_backend.domain.errors import ReportNotFoundError, UpstreamServiceError


class HttpReportReader:
    def __init__(self, base_url: str, *, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def list_reports(
        self, credential: str, *, experiment_id: UUID | None = None
    ) -> list[RemoteReport]:
        params = {"experiment_id": str(experiment_id)} if experiment_id is not None else {}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/reports",
                    params=params,
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("report-generator", str(exc)) from exc

        if response.status_code != 200:
            raise UpstreamServiceError(
                "report-generator", f"GET /reports returned {response.status_code}"
            )
        return [_parse_report(item) for item in response.json()]

    async def get_report(self, credential: str, report_id: UUID) -> RemoteReport:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/reports/{report_id}",
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("report-generator", str(exc)) from exc

        if response.status_code == 404:
            raise ReportNotFoundError(report_id)
        if response.status_code != 200:
            raise UpstreamServiceError(
                "report-generator", f"GET /reports/{report_id} returned {response.status_code}"
            )
        return _parse_report(response.json())


def _parse_report(payload: dict[str, Any]) -> RemoteReport:
    return RemoteReport(
        id=UUID(str(payload["id"])),
        experiment_id=UUID(str(payload["experiment_id"])),
        format=str(payload["format"]),
        status=str(payload["status"]),
        error_message=payload["error_message"],
        created_at=datetime.fromisoformat(str(payload["created_at"])),
        completed_at=(
            datetime.fromisoformat(str(payload["completed_at"]))
            if payload.get("completed_at") is not None
            else None
        ),
    )
