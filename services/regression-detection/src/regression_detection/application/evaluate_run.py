"""Use case: gate a completed eval run against its prompt's own history.

The baseline is *recomputed from every other completed run for this
prompt* on each call, not read from a stored running average — see
`Baseline`'s docstring for why. The verdict is a simple z-score check:
how many standard deviations below the historical mean is this run's
score?
"""

from __future__ import annotations

import statistics
from datetime import UTC, datetime
from uuid import UUID, uuid4

from regression_detection.domain.entities import Baseline, GateDecision, GateVerdict
from regression_detection.domain.errors import RunNotCompletedError
from regression_detection.domain.ports import BaselineRepository, EvalRunReader, GateDecisionRepository


class EvaluateRunUseCase:
    def __init__(
        self,
        eval_run_reader: EvalRunReader,
        baseline_repo: BaselineRepository,
        gate_decision_repo: GateDecisionRepository,
        *,
        fail_threshold_stddev: float = 2.0,
        review_threshold_stddev: float = 1.0,
    ) -> None:
        self._eval_run_reader = eval_run_reader
        self._baseline_repo = baseline_repo
        self._gate_decision_repo = gate_decision_repo
        self._fail_threshold = fail_threshold_stddev
        self._review_threshold = review_threshold_stddev

    async def execute(self, *, org_id: UUID, credential: str, run_id: UUID) -> GateDecision:
        run = await self._eval_run_reader.get_run(credential, run_id)
        if run.status != "completed" or run.aggregate_score is None:
            raise RunNotCompletedError(run_id)

        history = await self._eval_run_reader.list_runs(credential, prompt_id=run.prompt_id)
        prior_scores = [
            r.aggregate_score
            for r in history
            if r.id != run.id and r.status == "completed" and r.aggregate_score is not None
        ]

        now = datetime.now(UTC)
        if not prior_scores:
            # First completed run for this prompt — nothing to regress
            # against yet, so it passes by definition and becomes the seed
            # of the baseline.
            mean_score, stddev_score, sample_size = run.aggregate_score, 0.0, 1
            verdict = GateVerdict.PASS
        else:
            mean_score = statistics.fmean(prior_scores)
            stddev_score = statistics.pstdev(prior_scores) if len(prior_scores) > 1 else 0.0
            sample_size = len(prior_scores)
            verdict = self._verdict_for(run.aggregate_score, mean_score, stddev_score)

        await self._baseline_repo.upsert(
            Baseline(
                id=uuid4(),
                org_id=org_id,
                prompt_id=run.prompt_id,
                mean_score=mean_score,
                stddev_score=stddev_score,
                sample_size=sample_size,
                updated_at=now,
            )
        )

        decision = GateDecision(
            id=uuid4(),
            org_id=org_id,
            prompt_id=run.prompt_id,
            run_id=run.id,
            observed_score=run.aggregate_score,
            baseline_mean=mean_score,
            baseline_stddev=stddev_score,
            verdict=verdict,
            created_at=now,
        )
        await self._gate_decision_repo.create(decision)
        return decision

    def _verdict_for(self, observed: float, mean: float, stddev: float) -> GateVerdict:
        if stddev == 0:
            return GateVerdict.PASS if observed >= mean else GateVerdict.FAIL

        stddevs_below_mean = (mean - observed) / stddev
        if stddevs_below_mean >= self._fail_threshold:
            return GateVerdict.FAIL
        if stddevs_below_mean >= self._review_threshold:
            return GateVerdict.NEEDS_REVIEW
        return GateVerdict.PASS
