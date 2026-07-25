from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from prompt_registry.domain.entities import PromotionEvent, Prompt, PromptVersion
from prompt_registry.infrastructure.models import PromotionEventModel, PromptModel, PromptVersionModel


class SqlAlchemyPromptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, prompt: Prompt) -> None:
        self._session.add(
            PromptModel(
                id=prompt.id, org_id=prompt.org_id, name=prompt.name, created_at=prompt.created_at
            )
        )
        await self._session.commit()

    async def get_by_id(self, prompt_id: UUID) -> Prompt | None:
        model = await self._session.get(PromptModel, prompt_id)
        return _to_domain_prompt(model) if model else None

    async def get_by_org_and_name(self, org_id: UUID, name: str) -> Prompt | None:
        model = await self._session.scalar(
            select(PromptModel).where(PromptModel.org_id == org_id, PromptModel.name == name)
        )
        return _to_domain_prompt(model) if model else None


class SqlAlchemyPromptVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, version: PromptVersion) -> None:
        self._session.add(
            PromptVersionModel(
                id=version.id,
                prompt_id=version.prompt_id,
                template=version.template,
                variables_schema=version.variables_schema,
                semver_tag=version.semver_tag,
                created_at=version.created_at,
            )
        )
        await self._session.commit()

    async def get_by_id(self, version_id: UUID) -> PromptVersion | None:
        model = await self._session.get(PromptVersionModel, version_id)
        return _to_domain_version(model) if model else None

    async def list_by_prompt(self, prompt_id: UUID) -> list[PromptVersion]:
        models = await self._session.scalars(
            select(PromptVersionModel)
            .where(PromptVersionModel.prompt_id == prompt_id)
            .order_by(PromptVersionModel.created_at)
        )
        return [_to_domain_version(m) for m in models]


class SqlAlchemyPromotionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, event: PromotionEvent) -> None:
        self._session.add(
            PromotionEventModel(
                id=event.id,
                prompt_id=event.prompt_id,
                version_id=event.version_id,
                environment=event.environment,
                created_at=event.created_at,
            )
        )
        await self._session.commit()

    async def get_active(self, prompt_id: UUID, environment: str) -> PromotionEvent | None:
        model = await self._session.scalar(
            select(PromotionEventModel)
            .where(
                PromotionEventModel.prompt_id == prompt_id,
                PromotionEventModel.environment == environment,
            )
            .order_by(desc(PromotionEventModel.created_at))
            .limit(1)
        )
        return _to_domain_promotion(model) if model else None


def _to_domain_prompt(model: PromptModel) -> Prompt:
    return Prompt(id=model.id, org_id=model.org_id, name=model.name, created_at=model.created_at)


def _to_domain_version(model: PromptVersionModel) -> PromptVersion:
    return PromptVersion(
        id=model.id,
        prompt_id=model.prompt_id,
        template=model.template,
        variables_schema=model.variables_schema,
        semver_tag=model.semver_tag,
        created_at=model.created_at,
    )


def _to_domain_promotion(model: PromotionEventModel) -> PromotionEvent:
    return PromotionEvent(
        id=model.id,
        prompt_id=model.prompt_id,
        version_id=model.version_id,
        environment=model.environment,
        created_at=model.created_at,
    )
