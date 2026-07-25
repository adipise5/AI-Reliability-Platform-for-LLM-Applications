from __future__ import annotations

from uuid import uuid4

import pytest
from auth_client.models import IntrospectionResult
from fastapi.testclient import TestClient

from hallucination_detection.api import deps
from hallucination_detection.api.main import create_app
from hallucination_detection.application.check_faithfulness import CheckFaithfulnessUseCase
from hallucination_detection.application.get_check import GetCheckUseCase
from hallucination_detection.domain.entities import Verdict
from tests.unit.conftest import FakeClaimExtractor, FakeClaimVerifier, FakeFaithfulnessCheckRepository


@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def repo():
    return FakeFaithfulnessCheckRepository()


@pytest.fixture
def client(app, repo, org_id):
    app.dependency_overrides[deps.get_check_faithfulness_use_case] = lambda: CheckFaithfulnessUseCase(
        FakeClaimExtractor(["a claim"]), FakeClaimVerifier(Verdict.SUPPORTED), repo
    )
    app.dependency_overrides[deps.get_get_check_use_case] = lambda: GetCheckUseCase(repo)
    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:test", org_id=str(org_id), scopes=frozenset({"chat:write"})
    )
    app.dependency_overrides[deps.get_bearer_credential] = lambda: "fake-bearer-token"
    yield TestClient(app)
    app.dependency_overrides.clear()
