from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from hallucination_detection.domain.entities import Claim, FaithfulnessCheck, Verdict
from hallucination_detection.infrastructure.models import FaithfulnessCheckModel


class SqlAlchemyFaithfulnessCheckRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, check: FaithfulnessCheck) -> None:
        self._session.add(
            FaithfulnessCheckModel(
                id=check.id,
                org_id=check.org_id,
                response=check.response,
                context=check.context,
                claims=[
                    {"text": c.text, "verdict": c.verdict.value, "evidence": c.evidence}
                    for c in check.claims
                ],
                created_at=check.created_at,
            )
        )
        await self._session.commit()

    async def get_by_id(self, check_id: UUID) -> FaithfulnessCheck | None:
        model = await self._session.get(FaithfulnessCheckModel, check_id)
        return _to_domain(model) if model else None


def _to_domain(model: FaithfulnessCheckModel) -> FaithfulnessCheck:
    return FaithfulnessCheck(
        id=model.id,
        org_id=model.org_id,
        response=model.response,
        context=model.context,
        claims=tuple(
            Claim(text=c["text"], verdict=Verdict(c["verdict"]), evidence=c["evidence"])
            for c in model.claims
        ),
        created_at=model.created_at,
    )
