from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.unit.conftest import FakeSpanRepository
from trace_collector.api import deps
from trace_collector.api.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def repo():
    return FakeSpanRepository()


@pytest.fixture
def client(app, repo):
    app.dependency_overrides[deps.get_span_repo] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()
