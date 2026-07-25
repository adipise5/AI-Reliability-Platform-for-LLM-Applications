from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from notification_service.api.routers import channels, health, notifications
from notification_service.api.schemas import ErrorOut
from notification_service.domain.errors import (
    ChannelDisabledError,
    ChannelNotFoundError,
    NotificationNotFoundError,
    NotificationServiceError,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Notification Service",
        version="0.1.0",
        description="Slack/email/webhook delivery for org-scoped notification channels.",
    )

    # Standard request-count/latency histograms at GET /metrics — see
    # docs/deployment.md's Grafana section for the dashboard that reads them.
    Instrumentator().instrument(app).expose(app)

    app.include_router(health.router)
    app.include_router(channels.router)
    app.include_router(notifications.router)

    @app.exception_handler(ChannelNotFoundError)
    async def _channel_not_found(_: Request, exc: ChannelNotFoundError) -> JSONResponse:
        body = ErrorOut(type="channel_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(ChannelDisabledError)
    async def _channel_disabled(_: Request, exc: ChannelDisabledError) -> JSONResponse:
        body = ErrorOut(type="channel_disabled", message=str(exc))
        return JSONResponse(status_code=409, content=body.model_dump())

    @app.exception_handler(NotificationNotFoundError)
    async def _notification_not_found(_: Request, exc: NotificationNotFoundError) -> JSONResponse:
        body = ErrorOut(type="notification_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(NotificationServiceError)
    async def _domain_error(_: Request, exc: NotificationServiceError) -> JSONResponse:
        body = ErrorOut(type="notification_service_error", message=str(exc))
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
