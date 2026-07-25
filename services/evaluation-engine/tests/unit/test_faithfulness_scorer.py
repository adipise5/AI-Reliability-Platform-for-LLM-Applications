from __future__ import annotations

from evaluation_engine.infrastructure.scorers.faithfulness import FaithfulnessScorer


class _FakeHallucinationClient:
    def __init__(self, score: float = 1.0, claim_count: int = 2) -> None:
        self._score = score
        self._claim_count = claim_count
        self.calls: list[dict[str, object]] = []

    async def check_faithfulness(self, credential, *, model, response, context):
        self.calls.append({"model": model, "response": response, "context": context})
        return self._score, self._claim_count


async def test_score_skips_when_no_context_in_item_input():
    client = _FakeHallucinationClient()
    scorer = FaithfulnessScorer(client, judge_model="claude-sonnet-5")

    score = await scorer.score(
        credential="tok", output="an answer", expected_output="x", context={"item_input": {"q": "hi"}}
    )

    assert score.value == 1.0
    assert score.evidence["skipped"]
    assert client.calls == []


async def test_score_checks_faithfulness_when_context_present():
    client = _FakeHallucinationClient(score=0.5, claim_count=4)
    scorer = FaithfulnessScorer(client, judge_model="claude-sonnet-5")

    score = await scorer.score(
        credential="tok",
        output="an answer",
        expected_output="x",
        context={"item_input": {"context": "source passage"}},
    )

    assert score.value == 0.5
    assert score.evidence["claim_count"] == 4
    assert client.calls[0]["response"] == "an answer"
    assert client.calls[0]["context"] == "source passage"


async def test_score_handles_missing_item_input_key():
    client = _FakeHallucinationClient()
    scorer = FaithfulnessScorer(client, judge_model="claude-sonnet-5")

    score = await scorer.score(credential="tok", output="x", expected_output="y", context={})

    assert score.value == 1.0
    assert client.calls == []
