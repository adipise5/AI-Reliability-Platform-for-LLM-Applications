from __future__ import annotations

import pytest

from evaluation_engine.domain.errors import UnknownScorerError
from evaluation_engine.infrastructure.scorers.exact_match import ExactMatchScorer
from evaluation_engine.infrastructure.scorers.registry import InMemoryScorerRegistry


def test_get_returns_a_registered_scorer():
    registry = InMemoryScorerRegistry([ExactMatchScorer()])

    scorer = registry.get("exact_match")

    assert scorer.name == "exact_match"


def test_get_raises_for_an_unregistered_name():
    registry = InMemoryScorerRegistry([ExactMatchScorer()])

    with pytest.raises(UnknownScorerError):
        registry.get("nonexistent")
