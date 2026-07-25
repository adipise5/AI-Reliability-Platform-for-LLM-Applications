from __future__ import annotations

from uuid import uuid4

from experiment_tracking.application.get_score_history import GetScoreHistoryUseCase
from tests.unit.conftest import FakeEvalRunReader, make_run_summary


async def test_execute_delegates_to_the_evaluation_engine_by_prompt_id():
    prompt_id = uuid4()
    matching = make_run_summary(prompt_id=prompt_id)
    other = make_run_summary()
    reader = FakeEvalRunReader({matching.id: matching, other.id: other})
    use_case = GetScoreHistoryUseCase(reader)

    runs = await use_case.execute(credential="tok", prompt_id=prompt_id)

    assert runs == [matching]
    assert reader.list_runs_calls == [{"prompt_id": prompt_id, "dataset_id": None}]
