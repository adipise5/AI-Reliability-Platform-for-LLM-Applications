from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from notification_service.domain.entities import ChannelType, NotificationChannel
from notification_service.domain.ports import NotificationChannelRepository


class CreateChannelUseCase:
    def __init__(self, channel_repo: NotificationChannelRepository) -> None:
        self._channel_repo = channel_repo

    async def execute(
        self, *, org_id: UUID, channel_type: ChannelType, name: str, target: str
    ) -> NotificationChannel:
        channel = NotificationChannel(
            id=uuid4(),
            org_id=org_id,
            channel_type=channel_type,
            name=name,
            target=target,
            enabled=True,
            created_at=datetime.now(UTC),
        )
        await self._channel_repo.create(channel)
        return channel
