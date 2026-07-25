from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, Query

from dashboard_backend.api.deps import (
    get_bearer_credential,
    get_list_channels_use_case,
    get_list_notifications_use_case,
    require_principal,
)
from dashboard_backend.api.schemas import RemoteChannelOut, RemoteNotificationOut
from dashboard_backend.application.list_channels import ListChannelsUseCase
from dashboard_backend.application.list_notifications import ListNotificationsUseCase

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.get("/channels", response_model=list[RemoteChannelOut])
async def list_channels(
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[ListChannelsUseCase, Depends(get_list_channels_use_case)],
) -> list[RemoteChannelOut]:
    channels = await use_case.execute(credential=credential)
    return [RemoteChannelOut.from_domain(c) for c in channels]


@router.get("", response_model=list[RemoteNotificationOut])
async def list_notifications(
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[ListNotificationsUseCase, Depends(get_list_notifications_use_case)],
    channel_id: UUID | None = Query(default=None),
) -> list[RemoteNotificationOut]:
    notifications = await use_case.execute(credential=credential, channel_id=channel_id)
    return [RemoteNotificationOut.from_domain(n) for n in notifications]
