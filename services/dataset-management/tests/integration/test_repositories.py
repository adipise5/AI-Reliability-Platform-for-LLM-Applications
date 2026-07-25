"""Repository tests against a real (if not Postgres) engine — see the
auth service's test_repositories.py for why SQLite + schema_translate_map
is close enough for CI."""

from __future__ import annotations

from dataclasses import replace as dc_replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from dataset_management.domain.entities import Dataset, DatasetItem
from dataset_management.infrastructure.db import Base
from dataset_management.infrastructure.repositories import (
    SqlAlchemyDatasetItemRepository,
    SqlAlchemyDatasetRepository,
)


def _assert_same_entity(fetched, expected) -> None:
    assert fetched.created_at.replace(tzinfo=None) == expected.created_at.replace(tzinfo=None)
    assert dc_replace(fetched, created_at=expected.created_at) == expected


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:").execution_options(
        schema_translate_map={"dataset_mgmt": None}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


async def test_dataset_repository_create_lookup_and_bump_version(session):
    repo = SqlAlchemyDatasetRepository(session)
    org_id = uuid4()
    dataset = Dataset(
        id=uuid4(), org_id=org_id, name="qa-golden-set", current_version=0, created_at=datetime.now(UTC)
    )

    await repo.create(dataset)

    by_id = await repo.get_by_id(dataset.id)
    by_name = await repo.get_by_org_and_name(org_id, "qa-golden-set")
    assert by_id is not None and by_name is not None
    _assert_same_entity(by_id, dataset)
    _assert_same_entity(by_name, dataset)

    await repo.set_current_version(dataset.id, 3)
    bumped = await repo.get_by_id(dataset.id)
    assert bumped is not None
    assert bumped.current_version == 3


async def test_item_repository_bulk_create_and_list_by_version(session):
    dataset_repo = SqlAlchemyDatasetRepository(session)
    item_repo = SqlAlchemyDatasetItemRepository(session)
    dataset = Dataset(
        id=uuid4(), org_id=uuid4(), name="d", current_version=2, created_at=datetime.now(UTC)
    )
    await dataset_repo.create(dataset)

    v1_item = DatasetItem(
        id=uuid4(),
        dataset_id=dataset.id,
        version=1,
        input={"q": "a"},
        expected_output="A",
        metadata={"difficulty": "easy"},
        created_at=datetime.now(UTC),
    )
    v2_item_1 = DatasetItem(
        id=uuid4(), dataset_id=dataset.id, version=2, input={"q": "b"}, created_at=datetime.now(UTC)
    )
    v2_item_2 = DatasetItem(
        id=uuid4(), dataset_id=dataset.id, version=2, input={"q": "c"}, created_at=datetime.now(UTC)
    )
    await item_repo.bulk_create([v1_item, v2_item_1, v2_item_2])

    v1_items = await item_repo.list_by_version(dataset.id, 1)
    v2_items = await item_repo.list_by_version(dataset.id, 2)

    assert len(v1_items) == 1
    _assert_same_entity(v1_items[0], v1_item)
    assert {i.id for i in v2_items} == {v2_item_1.id, v2_item_2.id}
