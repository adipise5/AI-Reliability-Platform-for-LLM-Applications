"""HTTP client for the Trace Collector — implements `TraceReader`. No
credential is forwarded: the Trace Collector's query API is open (see
its ADR-0004), so there's nothing to authenticate."""

from __future__ import annotations

import httpx

from dashboard_backend.domain.entities import RemoteTraceSummary
from dashboard_backend.domain.errors import UpstreamServiceError


class HttpTraceReader:
    def __init__(self, base_url: str, *, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def list_recent_traces(self, limit: int) -> list[RemoteTraceSummary]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/traces", params={"limit": limit}
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("trace-collector", str(exc)) from exc

        if response.status_code != 200:
            raise UpstreamServiceError(
                "trace-collector", f"GET /traces returned {response.status_code}"
            )
        return [
            RemoteTraceSummary(
                trace_id=str(item["trace_id"]),
                root_span_name=str(item["root_span_name"]),
                span_count=int(item["span_count"]),
                status=str(item["status"]),
                duration_ms=float(item["duration_ms"]),
            )
            for item in response.json()
        ]
