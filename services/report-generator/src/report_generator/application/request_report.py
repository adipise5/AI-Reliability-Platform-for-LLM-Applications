"""Use case: create a report record and hand it to the task queue.

Deliberately does no upstream validation (that the experiment actually
exists) before enqueueing — same reasoning as the Evaluation Engine's
`TriggerEvalRunUseCase`: this stays a fast, synchronous endpoint, and
`GenerateReportUseCase` fails the report with a clear error if the
experiment turns out not to resolve.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from report_generator.domain.entities import Report, ReportFormat, ReportStatus
from report_generator.domain.ports import ReportRepository, TaskQueue


class RequestReportUseCase:
    def __init__(self, report_repo: ReportRepository, task_queue: TaskQueue) -> None:
        self._report_repo = report_repo
        self._task_queue = task_queue

    async def execute(
        self, *, org_id: UUID, experiment_id: UUID, format: ReportFormat, credential: str
    ) -> Report:
        report = Report(
            id=uuid4(),
            org_id=org_id,
            experiment_id=experiment_id,
            format=format,
            status=ReportStatus.PENDING,
            created_at=datetime.now(UTC),
        )
        await self._report_repo.create(report)
        self._task_queue.enqueue_generate_report(report.id, credential)
        return report
