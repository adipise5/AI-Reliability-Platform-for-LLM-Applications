from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataset_management.domain.entities import Dataset, DatasetItem
from dataset_management.infrastructure.models import DatasetItemModel, DatasetModel


class SqlAlchemyDatasetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, dataset: Dataset) -> None:
        self._session.add(
            DatasetModel(
                id=dataset.id,
                org_id=dataset.org_id,
                name=dataset.name,
                current_version=dataset.current_version,
                created_at=dataset.created_at,
            )
        )
        await self._session.commit()

    async def get_by_id(self, dataset_id: UUID) -> Dataset | None:
        model = await self._session.get(DatasetModel, dataset_id)
        return _to_domain_dataset(model) if model else None

    async def get_by_org_and_name(self, org_id: UUID, name: str) -> Dataset | None:
        model = await self._session.scalar(
            select(DatasetModel).where(DatasetModel.org_id == org_id, DatasetModel.name == name)
        )
        return _to_domain_dataset(model) if model else None

    async def set_current_version(self, dataset_id: UUID, version: int) -> None:
        model = await self._session.get(DatasetModel, dataset_id)
        assert model is not None, "set_current_version called for a dataset that doesn't exist"
        model.current_version = version
        await self._session.commit()


class SqlAlchemyDatasetItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_create(self, items: list[DatasetItem]) -> None:
        self._session.add_all(
            DatasetItemModel(
                id=item.id,
                dataset_id=item.dataset_id,
                version=item.version,
                input=item.input,
                expected_output=item.expected_output,
                item_metadata=item.metadata,
                created_at=item.created_at,
            )
            for item in items
        )
        await self._session.commit()

    async def list_by_version(self, dataset_id: UUID, version: int) -> list[DatasetItem]:
        models = await self._session.scalars(
            select(DatasetItemModel)
            .where(DatasetItemModel.dataset_id == dataset_id, DatasetItemModel.version == version)
            .order_by(DatasetItemModel.created_at)
        )
        return [_to_domain_item(m) for m in models]


def _to_domain_dataset(model: DatasetModel) -> Dataset:
    return Dataset(
        id=model.id,
        org_id=model.org_id,
        name=model.name,
        current_version=model.current_version,
        created_at=model.created_at,
    )


def _to_domain_item(model: DatasetItemModel) -> DatasetItem:
    return DatasetItem(
        id=model.id,
        dataset_id=model.dataset_id,
        version=model.version,
        input=model.input,
        expected_output=model.expected_output,
        metadata=model.item_metadata,
        created_at=model.created_at,
    )
