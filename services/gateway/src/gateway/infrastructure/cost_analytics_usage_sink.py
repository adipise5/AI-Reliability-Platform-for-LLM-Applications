"""The real `UsageSink` adapter, backed by Cost Analytics (Week 9).

Ingestion is a plain, unauthenticated POST — same "trusted internal
network" reasoning as the Trace Collector's ingestion endpoint (ADR-0004).
Any failure is logged and swallowed, never raised: a chat request must
never fail because the cost ledger is unreachable. Unlike tracing, this
call is awaited inline rather than backgrounded through a batching layer
— see ADR-0006 for that tradeoff.
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger("gateway.cost_analytics")


class HttpCostAnalyticsUsageSink:
    def __init__(self, base_url: str, *, timeout: float = 5.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def emit_usage(
        self,
        *,
        org_id: str,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        try:
            response = await self._client.post(
                "/api/v1/usage-events",
                json={
                    "org_id": org_id,
                    "provider": provider,
                    "model": model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                },
            )
            response.raise_for_status()
        except Exception:
            logger.warning("failed to record usage event with cost analytics", exc_info=True)
