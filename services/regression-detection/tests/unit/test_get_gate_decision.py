from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from regression_detection.application.get_gate_decision import GetGateDecisionUseCase
from regression_detection.domain.entities import GateDecision, GateVerdict
from regression_detection.domain.errors import GateDecisionNotFoundError
from tests.unit.conftest import FakeGateDecisionRepository


def make_decision(org_id, prompt_id, run_id, **overrides):
    base = GateDecision(
        id=uuid4(),
        org_id=org_id,
        prompt_id=prompt_id,
        run_id=run_id,
        observed_score=0.9,
        baseline_mean=0.9,
        baseline_stddev=0.0,
        verdict=GateVerdict.PASS,
        created_at=datetime.now(UTC),
    )
    return replace(base, **overrides)


async def test_returns_latest_decision_for_run(org_id):
    run_id = uuid4()
    repo = FakeGateDecisionRepository()
    await repo.create(make_decision(org_id, uuid4(), run_id))
    use_case = GetGateDecisionUseCase(repo)

    decision = await use_case.execute(org_id=org_id, run_id=run_id)

    assert decision.run_id == run_id


async def test_raises_when_no_decision_recorded(org_id):
    repo = FakeGateDecisionRepository()
    use_case = GetGateDecisionUseCase(repo)

    with pytest.raises(GateDecisionNotFoundError):
        await use_case.execute(org_id=org_id, run_id=uuid4())


async def test_raises_when_decision_belongs_to_a_different_org(org_id):
    run_id = uuid4()
    repo = FakeGateDecisionRepository()
    await repo.create(make_decision(uuid4(), uuid4(), run_id))
    use_case = GetGateDecisionUseCase(repo)

    with pytest.raises(GateDecisionNotFoundError):
        await use_case.execute(org_id=org_id, run_id=run_id)
