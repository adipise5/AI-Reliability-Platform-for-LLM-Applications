from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from dashboard_backend.api.routers import (
    cost,
    dashboard,
    github,
    health,
    notifications,
    regression,
    reports,
    runs,
    traces,
)
from dashboard_backend.api.schemas import ErrorOut
from dashboard_backend.domain.errors import (
    DashboardBackendError,
    ReportNotFoundError,
    RunNotFoundError,
    UpstreamServiceError,
)
from dashboard_backend.infrastructure.config import get_settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Dashboard Backend",
        version="0.1.0",
        description="Backend-for-frontend: aggregated, read-only view models for the React Dashboard.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Standard request-count/latency histograms at GET /metrics — see
    # docs/deployment.md's Grafana section for the dashboard that reads them.
    Instrumentator().instrument(app).expose(app)

    app.include_router(health.router)
    app.include_router(dashboard.router)
    app.include_router(runs.router)
    app.include_router(cost.router)
    app.include_router(regression.router)
    app.include_router(reports.router)
    app.include_router(notifications.router)
    app.include_router(github.router)
    app.include_router(traces.router)

    @app.exception_handler(RunNotFoundError)
    async def _run_not_found(_: Request, exc: RunNotFoundError) -> JSONResponse:
        body = ErrorOut(type="run_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(ReportNotFoundError)
    async def _report_not_found(_: Request, exc: ReportNotFoundError) -> JSONResponse:
        body = ErrorOut(type="report_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(UpstreamServiceError)
    async def _upstream_error(_: Request, exc: UpstreamServiceError) -> JSONResponse:
        body = ErrorOut(type="upstream_service_error", message=str(exc))
        return JSONResponse(status_code=502, content=body.model_dump())

    @app.exception_handler(DashboardBackendError)
    async def _domain_error(_: Request, exc: DashboardBackendError) -> JSONResponse:
        body = ErrorOut(type="dashboard_backend_error", message=str(exc))
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
