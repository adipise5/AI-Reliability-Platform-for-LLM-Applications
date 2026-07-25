from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from github_integration.domain.entities import CheckConclusion, CheckRun, CheckStatus
from github_integration.infrastructure.models import CheckRunModel


class SqlAlchemyCheckRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, check: CheckRun) -> None:
        self._session.add(
            CheckRunModel(
                id=check.id,
                org_id=check.org_id,
                repo=check.repo,
                commit_sha=check.commit_sha,
                github_check_run_id=check.github_check_run_id,
                status=check.status.value,
                conclusion=check.conclusion.value if check.conclusion is not None else None,
                run_id=check.run_id,
                created_at=check.created_at,
                completed_at=check.completed_at,
            )
        )
        await self._session.commit()

    async def get_by_id(self, check_id: UUID) -> CheckRun | None:
        model = await self._session.get(CheckRunModel, check_id)
        if model is None:
            return None
        return _to_domain(model)

    async def update(self, check: CheckRun) -> None:
        model = await self._session.get(CheckRunModel, check.id)
        assert model is not None
        model.status = check.status.value
        model.conclusion = check.conclusion.value if check.conclusion is not None else None
        model.run_id = check.run_id
        model.completed_at = check.completed_at
        await self._session.commit()

    async def list_by_org(
        self, org_id: UUID, *, repo: str | None = None, commit_sha: str | None = None
    ) -> list[CheckRun]:
        stmt = select(CheckRunModel).where(CheckRunModel.org_id == org_id)
        if repo is not None:
            stmt = stmt.where(CheckRunModel.repo == repo)
        if commit_sha is not None:
            stmt = stmt.where(CheckRunModel.commit_sha == commit_sha)
        stmt = stmt.order_by(CheckRunModel.created_at.desc())
        result = await self._session.scalars(stmt)
        return [_to_domain(model) for model in result]


def _to_domain(model: CheckRunModel) -> CheckRun:
    return CheckRun(
        id=model.id,
        org_id=model.org_id,
        repo=model.repo,
        commit_sha=model.commit_sha,
        github_check_run_id=model.github_check_run_id,
        status=CheckStatus(model.status),
        conclusion=CheckConclusion(model.conclusion) if model.conclusion is not None else None,
        run_id=model.run_id,
        created_at=model.created_at,
        completed_at=model.completed_at,
    )
