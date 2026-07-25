from __future__ import annotations

from uuid import UUID

from notification_service.domain.entities import NotificationChannel
from notification_service.domain.errors import ChannelNotFoundError
from notification_service.domain.ports import NotificationChannelRepository


class GetChannelUseCase:
    def __init__(self, channel_repo: NotificationChannelRepository) -> None:
        self._channel_repo = channel_repo

    async def execute(self, *, org_id: UUID, channel_id: UUID) -> NotificationChannel:
        channel = await self._channel_repo.get_by_id(channel_id)
        if channel is None or channel.org_id != org_id:
            raise ChannelNotFoundError(channel_id)
        return channel
