from __future__ import annotations

from uuid import uuid4

import pytest
from auth_client.models import IntrospectionResult
from fastapi.testclient import TestClient

from github_integration.api import deps
from github_integration.api.main import create_app
from github_integration.application.complete_check import CompleteCheckUseCase
from github_integration.application.get_check import GetCheckUseCase
from github_integration.application.handle_webhook import HandleWebhookUseCase
from github_integration.application.list_checks import ListChecksUseCase
from github_integration.application.post_pr_comment import PostPrCommentUseCase
from tests.unit.conftest import FakeCheckRunRepository, FakeGateDecisionReader, FakeGitHubClient

WEBHOOK_SECRET = "s3cr3t"


@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def check_repo():
    return FakeCheckRunRepository()


@pytest.fixture
def github():
    return FakeGitHubClient()


@pytest.fixture
def reader():
    return FakeGateDecisionReader()


@pytest.fixture
def client(app, check_repo, github, reader, org_id):
    app.dependency_overrides[deps.get_handle_webhook_use_case] = lambda: HandleWebhookUseCase(
        check_repo, github, WEBHOOK_SECRET
    )
    app.dependency_overrides[deps.get_complete_check_use_case] = lambda: CompleteCheckUseCase(
        check_repo, reader, github
    )
    app.dependency_overrides[deps.get_post_pr_comment_use_case] = lambda: PostPrCommentUseCase(
        check_repo, github
    )
    app.dependency_overrides[deps.get_get_check_use_case] = lambda: GetCheckUseCase(check_repo)
    app.dependency_overrides[deps.get_list_checks_use_case] = lambda: ListChecksUseCase(check_repo)
    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:test", org_id=str(org_id), scopes=frozenset({"chat:write"})
    )
    app.dependency_overrides[deps.get_bearer_credential] = lambda: "fake-bearer-token"
    yield TestClient(app)
    app.dependency_overrides.clear()
