from __future__ import annotations

from dashboard_backend.application.list_runs import ListRunsUseCase
from tests.unit.conftest import FakeEvalRunReader, make_run


async def test_returns_runs_from_the_reader():
    run = make_run()
    use_case = ListRunsUseCase(FakeEvalRunReader([run]))

    runs = await use_case.execute(credential="tok")

    assert runs == [run]
