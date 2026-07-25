from __future__ import annotations

from uuid import uuid4

import pytest
from auth_client.models import IntrospectionResult
from fastapi.testclient import TestClient

from notification_service.api import deps
from notification_service.api.main import create_app
from notification_service.application.create_channel import CreateChannelUseCase
from notification_service.application.delete_channel import DeleteChannelUseCase
from notification_service.application.get_channel import GetChannelUseCase
from notification_service.application.get_notification import GetNotificationUseCase
from notification_service.application.list_channels import ListChannelsUseCase
from notification_service.application.list_notifications import ListNotificationsUseCase
from notification_service.application.send_notification import SendNotificationUseCase
from tests.unit.conftest import FakeNotificationChannelRepository, FakeNotificationRepository, FakeTaskQueue


@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def channel_repo():
    return FakeNotificationChannelRepository()


@pytest.fixture
def notification_repo():
    return FakeNotificationRepository()


@pytest.fixture
def queue():
    return FakeTaskQueue()


@pytest.fixture
def client(app, channel_repo, notification_repo, queue, org_id):
    app.dependency_overrides[deps.get_create_channel_use_case] = lambda: CreateChannelUseCase(
        channel_repo
    )
    app.dependency_overrides[deps.get_list_channels_use_case] = lambda: ListChannelsUseCase(
        channel_repo
    )
    app.dependency_overrides[deps.get_get_channel_use_case] = lambda: GetChannelUseCase(channel_repo)
    app.dependency_overrides[deps.get_delete_channel_use_case] = lambda: DeleteChannelUseCase(
        channel_repo
    )
    app.dependency_overrides[deps.get_send_notification_use_case] = lambda: SendNotificationUseCase(
        channel_repo, notification_repo, queue
    )
    app.dependency_overrides[deps.get_get_notification_use_case] = lambda: GetNotificationUseCase(
        notification_repo
    )
    app.dependency_overrides[deps.get_list_notifications_use_case] = (
        lambda: ListNotificationsUseCase(notification_repo)
    )
    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:test", org_id=str(org_id), scopes=frozenset({"chat:write"})
    )
    yield TestClient(app)
    app.dependency_overrides.clear()
