from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from trace_collector.domain.entities import Span, SpanStatus
from trace_collector.infrastructure.models import SpanModel


class SqlAlchemySpanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_batch(self, spans: list[Span]) -> None:
        self._session.add_all(
            SpanModel(
                id=UUID(span.id),
                trace_id=span.trace_id,
                span_id=span.span_id,
                parent_span_id=span.parent_span_id,
                name=span.name,
                status=span.status.value,
                start_time=span.start_time,
                end_time=span.end_time,
                attributes=span.attributes,
            )
            for span in spans
        )
        await self._session.commit()

    async def get_by_trace_id(self, trace_id: str) -> list[Span]:
        models = await self._session.scalars(
            select(SpanModel).where(SpanModel.trace_id == trace_id).order_by(SpanModel.start_time)
        )
        return [_to_domain(m) for m in models]

    async def list_recent_trace_ids(self, limit: int) -> list[str]:
        rows = await self._session.execute(
            select(SpanModel.trace_id, func.max(SpanModel.end_time).label("last_end"))
            .group_by(SpanModel.trace_id)
            .order_by(desc("last_end"))
            .limit(limit)
        )
        return [row.trace_id for row in rows]


def _to_domain(model: SpanModel) -> Span:
    return Span(
        id=str(model.id),
        trace_id=model.trace_id,
        span_id=model.span_id,
        parent_span_id=model.parent_span_id,
        name=model.name,
        status=SpanStatus(model.status),
        start_time=model.start_time,
        end_time=model.end_time,
        attributes=model.attributes,
    )
