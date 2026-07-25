"""Use case: finish a check once its eval run's gate decision is in.

Called by a CI workflow after it has triggered an eval run and waited for
Regression Detection to gate it — this use case does the translation from
a statistical verdict to a GitHub check conclusion, and is the only place
that translation happens.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from github_integration.domain.entities import CheckConclusion, CheckRun, CheckStatus
from github_integration.domain.errors import CheckAlreadyCompletedError, CheckNotFoundError
from github_integration.domain.ports import CheckRunRepository, GateDecisionReader, GitHubClient

_CONCLUSION_FOR_VERDICT: dict[str, CheckConclusion] = {
    "pass": CheckConclusion.SUCCESS,
    "fail": CheckConclusion.FAILURE,
    "needs_review": CheckConclusion.NEUTRAL,
}


class CompleteCheckUseCase:
    def __init__(
        self,
        check_repo: CheckRunRepository,
        gate_decision_reader: GateDecisionReader,
        github_client: GitHubClient,
    ) -> None:
        self._check_repo = check_repo
        self._gate_decision_reader = gate_decision_reader
        self._github_client = github_client

    async def execute(
        self, *, org_id: UUID, credential: str, check_id: UUID, run_id: UUID
    ) -> CheckRun:
        check = await self._check_repo.get_by_id(check_id)
        if check is None or check.org_id != org_id:
            raise CheckNotFoundError(check_id)
        if check.status == CheckStatus.COMPLETED:
            raise CheckAlreadyCompletedError(check_id)

        decision = await self._gate_decision_reader.get_gate_decision(credential, run_id)
        conclusion = _CONCLUSION_FOR_VERDICT.get(decision.verdict, CheckConclusion.NEUTRAL)
        summary = (
            f"Verdict: **{decision.verdict}**\n\n"
            f"Observed score: {decision.observed_score:.4f}\n"
            f"Baseline: {decision.baseline_mean:.4f} ± {decision.baseline_stddev:.4f}"
        )

        await self._github_client.update_check_run(
            repo=check.repo,
            check_run_id=check.github_check_run_id,
            status=CheckStatus.COMPLETED,
            conclusion=conclusion,
            summary=summary,
        )

        completed = replace(
            check,
            status=CheckStatus.COMPLETED,
            conclusion=conclusion,
            run_id=run_id,
            completed_at=datetime.now(UTC),
        )
        await self._check_repo.update(completed)
        return completed
