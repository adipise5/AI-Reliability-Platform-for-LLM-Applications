from __future__ import annotations

from collections.abc import Iterable

from evaluation_engine.domain.errors import UnknownScorerError
from evaluation_engine.domain.ports import Scorer


class InMemoryScorerRegistry:
    def __init__(self, scorers: Iterable[Scorer]) -> None:
        self._scorers = {scorer.name: scorer for scorer in scorers}

    def get(self, name: str) -> Scorer:
        try:
            return self._scorers[name]
        except KeyError:
            raise UnknownScorerError(name) from None
