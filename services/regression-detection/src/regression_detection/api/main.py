from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from regression_detection.api.routers import baselines, gate_decisions, health, latency_anomaly
from regression_detection.api.schemas import ErrorOut
from regression_detection.domain.errors import (
    BaselineNotFoundError,
    GateDecisionNotFoundError,
    RegressionDetectionError,
    RunNotCompletedError,
    UpstreamServiceError,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Regression Detection Engine",
        version="0.1.0",
        description="Statistical CI gating for eval runs, and latency-anomaly checks over recent traces.",
    )

    # Standard request-count/latency histograms at GET /metrics — see
    # docs/deployment.md's Grafana section for the dashboard that reads them.
    Instrumentator().instrument(app).expose(app)

    app.include_router(health.router)
    app.include_router(gate_decisions.router)
    app.include_router(baselines.router)
    app.include_router(latency_anomaly.router)

    @app.exception_handler(RunNotCompletedError)
    async def _run_not_completed(_: Request, exc: RunNotCompletedError) -> JSONResponse:
        body = ErrorOut(type="run_not_completed", message=str(exc))
        return JSONResponse(status_code=409, content=body.model_dump())

    @app.exception_handler(GateDecisionNotFoundError)
    async def _gate_decision_not_found(_: Request, exc: GateDecisionNotFoundError) -> JSONResponse:
        body = ErrorOut(type="gate_decision_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(BaselineNotFoundError)
    async def _baseline_not_found(_: Request, exc: BaselineNotFoundError) -> JSONResponse:
        body = ErrorOut(type="baseline_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(UpstreamServiceError)
    async def _upstream_error(_: Request, exc: UpstreamServiceError) -> JSONResponse:
        body = ErrorOut(type="upstream_service_error", message=str(exc))
        return JSONResponse(status_code=502, content=body.model_dump())

    @app.exception_handler(RegressionDetectionError)
    async def _domain_error(_: Request, exc: RegressionDetectionError) -> JSONResponse:
        body = ErrorOut(type="regression_detection_error", message=str(exc))
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
