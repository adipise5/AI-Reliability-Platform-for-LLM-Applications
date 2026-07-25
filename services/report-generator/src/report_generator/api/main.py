from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from report_generator.api.routers import health, reports
from report_generator.api.schemas import ErrorOut
from report_generator.domain.errors import (
    ReportGeneratorError,
    ReportNotFoundError,
    ReportNotReadyError,
    UnsupportedReportFormatError,
    UpstreamServiceError,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Report Generator",
        version="0.1.0",
        description="Renders HTML/PDF reports summarizing an experiment's runs, generated asynchronously.",
    )

    app.include_router(health.router)
    app.include_router(reports.router)

    @app.exception_handler(ReportNotFoundError)
    async def _not_found(_: Request, exc: ReportNotFoundError) -> JSONResponse:
        body = ErrorOut(type="report_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(ReportNotReadyError)
    async def _not_ready(_: Request, exc: ReportNotReadyError) -> JSONResponse:
        body = ErrorOut(type="report_not_ready", message=str(exc))
        return JSONResponse(status_code=409, content=body.model_dump())

    @app.exception_handler(UnsupportedReportFormatError)
    async def _unsupported_format(_: Request, exc: UnsupportedReportFormatError) -> JSONResponse:
        body = ErrorOut(type="unsupported_report_format", message=str(exc))
        return JSONResponse(status_code=400, content=body.model_dump())

    @app.exception_handler(UpstreamServiceError)
    async def _upstream_error(_: Request, exc: UpstreamServiceError) -> JSONResponse:
        body = ErrorOut(type="upstream_service_error", message=str(exc))
        return JSONResponse(status_code=502, content=body.model_dump())

    @app.exception_handler(ReportGeneratorError)
    async def _domain_error(_: Request, exc: ReportGeneratorError) -> JSONResponse:
        body = ErrorOut(type="report_generator_error", message=str(exc))
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
