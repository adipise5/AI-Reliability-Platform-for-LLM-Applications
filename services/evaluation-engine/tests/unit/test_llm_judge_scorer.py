from __future__ import annotations

from evaluation_engine.domain.entities import RemoteCompletion
from evaluation_engine.infrastructure.scorers.llm_judge import LLMJudgeScorer
from tests.unit.conftest import FakeGatewayClient


def _completion(content: str) -> RemoteCompletion:
    return RemoteCompletion(content=content, prompt_tokens=1, completion_tokens=1, latency_ms=1.0)


async def test_score_parses_a_numeric_judge_response():
    gateway = FakeGatewayClient(_completion("0.8"))
    scorer = LLMJudgeScorer(gateway, judge_model="claude-sonnet-5")

    score = await scorer.score(
        credential="tok", output="a decent answer", expected_output="the answer", context={}
    )

    assert score.value == 0.8
    assert score.evidence["judge_model"] == "claude-sonnet-5"


async def test_score_calls_the_judge_model_at_zero_temperature():
    gateway = FakeGatewayClient(_completion("1"))
    scorer = LLMJudgeScorer(gateway, judge_model="claude-sonnet-5")

    await scorer.score(credential="tok", output="x", expected_output="x", context={})

    assert gateway.calls[0]["model"] == "claude-sonnet-5"
    assert gateway.calls[0]["temperature"] == 0.0


async def test_score_clamps_out_of_range_values():
    gateway = FakeGatewayClient(_completion("1.7"))
    scorer = LLMJudgeScorer(gateway, judge_model="claude-sonnet-5")

    score = await scorer.score(credential="tok", output="x", expected_output="y", context={})

    assert score.value == 1.0


async def test_score_defaults_to_zero_on_unparseable_judge_response():
    gateway = FakeGatewayClient(_completion("I think it's pretty good!"))
    scorer = LLMJudgeScorer(gateway, judge_model="claude-sonnet-5")

    score = await scorer.score(credential="tok", output="x", expected_output="y", context={})

    assert score.value == 0.0
    assert score.evidence["parse_error"] is True
