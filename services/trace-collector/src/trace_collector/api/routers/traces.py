from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from trace_collector.api.deps import (
    get_get_trace_use_case,
    get_ingest_spans_use_case,
    get_list_traces_use_case,
)
from trace_collector.api.schemas import IngestSpansIn, IngestSpansOut, SpanOut, TraceOut, TraceSummaryOut
from trace_collector.application.get_trace import GetTraceUseCase
from trace_collector.application.ingest_spans import IngestSpansUseCase
from trace_collector.application.list_traces import ListTracesUseCase

router = APIRouter(prefix="/api/v1/traces", tags=["traces"])


@router.post("", response_model=IngestSpansOut, status_code=status.HTTP_202_ACCEPTED)
async def ingest_spans(
    payload: IngestSpansIn,
    use_case: Annotated[IngestSpansUseCase, Depends(get_ingest_spans_use_case)],
) -> IngestSpansOut:
    ingested = await use_case.execute([span.to_domain() for span in payload.spans])
    return IngestSpansOut(ingested=ingested)


@router.get("", response_model=list[TraceSummaryOut])
async def list_traces(
    use_case: Annotated[ListTracesUseCase, Depends(get_list_traces_use_case)],
    limit: int = Query(default=20, ge=1, le=200),
) -> list[TraceSummaryOut]:
    summaries = await use_case.execute(limit=limit)
    return [TraceSummaryOut.from_domain(s) for s in summaries]


@router.get("/{trace_id}", response_model=TraceOut)
async def get_trace(
    trace_id: str,
    use_case: Annotated[GetTraceUseCase, Depends(get_get_trace_use_case)],
) -> TraceOut:
    spans = await use_case.execute(trace_id)
    return TraceOut(trace_id=trace_id, spans=[SpanOut.from_domain(s) for s in spans])
