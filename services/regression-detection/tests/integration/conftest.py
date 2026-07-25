from __future__ import annotations

from uuid import uuid4

import pytest
from auth_client.models import IntrospectionResult
from fastapi.testclient import TestClient

from regression_detection.api import deps
from regression_detection.api.main import create_app
from regression_detection.application.check_latency_anomaly import CheckLatencyAnomalyUseCase
from regression_detection.application.evaluate_run import EvaluateRunUseCase
from regression_detection.application.get_baseline import GetBaselineUseCase
from regression_detection.application.get_gate_decision import GetGateDecisionUseCase
from tests.unit.conftest import (
    FakeBaselineRepository,
    FakeEvalRunReader,
    FakeGateDecisionRepository,
    FakeTraceReader,
)


@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def baselines():
    return FakeBaselineRepository()


@pytest.fixture
def decisions():
    return FakeGateDecisionRepository()


@pytest.fixture
def reader():
    return FakeEvalRunReader()


@pytest.fixture
def trace_reader():
    return FakeTraceReader()


@pytest.fixture
def client(app, baselines, decisions, reader, trace_reader, org_id):
    app.dependency_overrides[deps.get_evaluate_run_use_case] = lambda: EvaluateRunUseCase(
        reader, baselines, decisions
    )
    app.dependency_overrides[deps.get_get_gate_decision_use_case] = lambda: GetGateDecisionUseCase(decisions)
    app.dependency_overrides[deps.get_get_baseline_use_case] = lambda: GetBaselineUseCase(baselines)
    app.dependency_overrides[deps.get_check_latency_anomaly_use_case] = lambda: CheckLatencyAnomalyUseCase(
        trace_reader
    )
    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:test", org_id=str(org_id), scopes=frozenset({"chat:write"})
    )
    app.dependency_overrides[deps.get_bearer_credential] = lambda: "fake-bearer-token"
    yield TestClient(app)
    app.dependency_overrides.clear()
