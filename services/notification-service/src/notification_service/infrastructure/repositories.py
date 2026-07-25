from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from notification_service.domain.entities import (
    ChannelType,
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from notification_service.infrastructure.models import NotificationChannelModel, NotificationModel


class SqlAlchemyNotificationChannelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, channel: NotificationChannel) -> None:
        self._session.add(
            NotificationChannelModel(
                id=channel.id,
                org_id=channel.org_id,
                channel_type=channel.channel_type.value,
                name=channel.name,
                target=channel.target,
                enabled=channel.enabled,
                created_at=channel.created_at,
            )
        )
        await self._session.commit()

    async def get_by_id(self, channel_id: UUID) -> NotificationChannel | None:
        model = await self._session.get(NotificationChannelModel, channel_id)
        if model is None:
            return None
        return _to_channel(model)

    async def list_by_org(self, org_id: UUID) -> list[NotificationChannel]:
        stmt = (
            select(NotificationChannelModel)
            .where(NotificationChannelModel.org_id == org_id)
            .order_by(NotificationChannelModel.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return [_to_channel(model) for model in result]

    async def delete(self, channel_id: UUID) -> None:
        await self._session.execute(
            delete(NotificationChannelModel).where(NotificationChannelModel.id == channel_id)
        )
        await self._session.commit()


class SqlAlchemyNotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, notification: Notification) -> None:
        self._session.add(
            NotificationModel(
                id=notification.id,
                org_id=notification.org_id,
                channel_id=notification.channel_id,
                subject=notification.subject,
                body=notification.body,
                status=notification.status.value,
                error_message=notification.error_message,
                created_at=notification.created_at,
                completed_at=notification.completed_at,
            )
        )
        await self._session.commit()

    async def get_by_id(self, notification_id: UUID) -> Notification | None:
        model = await self._session.get(NotificationModel, notification_id)
        if model is None:
            return None
        return _to_notification(model)

    async def update(self, notification: Notification) -> None:
        model = await self._session.get(NotificationModel, notification.id)
        assert model is not None
        model.status = notification.status.value
        model.error_message = notification.error_message
        model.completed_at = notification.completed_at
        await self._session.commit()

    async def list_by_org(
        self, org_id: UUID, *, channel_id: UUID | None = None
    ) -> list[Notification]:
        stmt = select(NotificationModel).where(NotificationModel.org_id == org_id)
        if channel_id is not None:
            stmt = stmt.where(NotificationModel.channel_id == channel_id)
        stmt = stmt.order_by(NotificationModel.created_at.desc())
        result = await self._session.scalars(stmt)
        return [_to_notification(model) for model in result]


def _to_channel(model: NotificationChannelModel) -> NotificationChannel:
    return NotificationChannel(
        id=model.id,
        org_id=model.org_id,
        channel_type=ChannelType(model.channel_type),
        name=model.name,
        target=model.target,
        enabled=model.enabled,
        created_at=model.created_at,
    )


def _to_notification(model: NotificationModel) -> Notification:
    return Notification(
        id=model.id,
        org_id=model.org_id,
        channel_id=model.channel_id,
        subject=model.subject,
        body=model.body,
        status=NotificationStatus(model.status),
        error_message=model.error_message,
        created_at=model.created_at,
        completed_at=model.completed_at,
    )
