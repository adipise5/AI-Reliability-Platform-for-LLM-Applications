from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from trace_collector.api.routers import health, traces
from trace_collector.api.schemas import ErrorOut
from trace_collector.domain.errors import EmptyBatchError, TraceCollectorError, TraceNotFoundError


def create_app() -> FastAPI:
    app = FastAPI(
        title="Trace Collector",
        version="0.1.0",
        description="OTel-shaped span ingestion, storage, and a basic trace viewer API.",
    )

    # Standard request-count/latency histograms at GET /metrics — see
    # docs/deployment.md's Grafana section for the dashboard that reads them.
    Instrumentator().instrument(app).expose(app)

    app.include_router(health.router)
    app.include_router(traces.router)

    @app.exception_handler(EmptyBatchError)
    async def _empty_batch(_: Request, exc: EmptyBatchError) -> JSONResponse:
        body = ErrorOut(type="empty_batch", message=str(exc))
        return JSONResponse(status_code=400, content=body.model_dump())

    @app.exception_handler(TraceNotFoundError)
    async def _not_found(_: Request, exc: TraceNotFoundError) -> JSONResponse:
        body = ErrorOut(type="trace_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(TraceCollectorError)
    async def _domain_error(_: Request, exc: TraceCollectorError) -> JSONResponse:
        body = ErrorOut(type="trace_collector_error", message=str(exc))
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
