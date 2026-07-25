from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, Query, status

from notification_service.api.deps import (
    get_get_notification_use_case,
    get_list_notifications_use_case,
    get_send_notification_use_case,
    org_id_of,
    require_principal,
)
from notification_service.api.schemas import NotificationOut, SendNotificationIn
from notification_service.application.get_notification import GetNotificationUseCase
from notification_service.application.list_notifications import ListNotificationsUseCase
from notification_service.application.send_notification import SendNotificationUseCase

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.post("", response_model=NotificationOut, status_code=status.HTTP_202_ACCEPTED)
async def send_notification(
    payload: SendNotificationIn,
    principal: Principal,
    use_case: Annotated[SendNotificationUseCase, Depends(get_send_notification_use_case)],
) -> NotificationOut:
    notification = await use_case.execute(
        org_id=org_id_of(principal),
        channel_id=payload.channel_id,
        subject=payload.subject,
        body=payload.body,
    )
    return NotificationOut.from_domain(notification)


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    principal: Principal,
    use_case: Annotated[ListNotificationsUseCase, Depends(get_list_notifications_use_case)],
    channel_id: UUID | None = Query(default=None),
) -> list[NotificationOut]:
    notifications = await use_case.execute(org_id=org_id_of(principal), channel_id=channel_id)
    return [NotificationOut.from_domain(n) for n in notifications]


@router.get("/{notification_id}", response_model=NotificationOut)
async def get_notification(
    notification_id: UUID,
    principal: Principal,
    use_case: Annotated[GetNotificationUseCase, Depends(get_get_notification_use_case)],
) -> NotificationOut:
    notification = await use_case.execute(org_id=org_id_of(principal), notification_id=notification_id)
    return NotificationOut.from_domain(notification)
