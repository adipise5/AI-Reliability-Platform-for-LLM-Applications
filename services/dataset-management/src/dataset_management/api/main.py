from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from dataset_management.api.routers import datasets, health
from dataset_management.api.schemas import ErrorOut
from dataset_management.domain.errors import (
    DatasetManagementError,
    DatasetNotFoundError,
    DuplicateDatasetNameError,
    EmptyImportError,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Dataset Management",
        version="0.1.0",
        description="Golden datasets: versioned bulk import/export for evaluation fixtures.",
    )

    app.include_router(health.router)
    app.include_router(datasets.router)

    @app.exception_handler(DuplicateDatasetNameError)
    async def _duplicate_name(_: Request, exc: DuplicateDatasetNameError) -> JSONResponse:
        body = ErrorOut(type="duplicate_dataset_name", message=str(exc))
        return JSONResponse(status_code=409, content=body.model_dump())

    @app.exception_handler(DatasetNotFoundError)
    async def _not_found(_: Request, exc: DatasetNotFoundError) -> JSONResponse:
        body = ErrorOut(type="dataset_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(EmptyImportError)
    async def _empty_import(_: Request, exc: EmptyImportError) -> JSONResponse:
        body = ErrorOut(type="empty_import", message=str(exc))
        return JSONResponse(status_code=400, content=body.model_dump())

    @app.exception_handler(DatasetManagementError)
    async def _domain_error(_: Request, exc: DatasetManagementError) -> JSONResponse:
        body = ErrorOut(type="dataset_management_error", message=str(exc))
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
