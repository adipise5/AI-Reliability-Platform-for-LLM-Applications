from __future__ import annotations

from evaluation_engine.infrastructure.scorers.exact_match import ExactMatchScorer


async def test_score_matches_on_exact_string_equality():
    scorer = ExactMatchScorer()

    score = await scorer.score(credential="tok", output="42", expected_output="42", context={})

    assert score.value == 1.0
    assert score.scorer_name == "exact_match"


async def test_score_trims_whitespace_before_comparing():
    scorer = ExactMatchScorer()

    score = await scorer.score(credential="tok", output=" 42 \n", expected_output="42", context={})

    assert score.value == 1.0


async def test_score_zero_on_mismatch():
    scorer = ExactMatchScorer()

    score = await scorer.score(credential="tok", output="41", expected_output="42", context={})

    assert score.value == 0.0
