from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, Query, status

from dataset_management.api.deps import (
    get_create_dataset_use_case,
    get_get_dataset_use_case,
    get_import_items_use_case,
    get_list_items_use_case,
    org_id_of,
    require_principal,
)
from dataset_management.api.schemas import (
    BulkImportIn,
    CreateDatasetIn,
    DatasetItemOut,
    DatasetOut,
    ImportResultOut,
)
from dataset_management.application.create_dataset import CreateDatasetUseCase
from dataset_management.application.get_dataset import GetDatasetUseCase
from dataset_management.application.import_items import ImportItemsUseCase
from dataset_management.application.list_items import ListItemsUseCase

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.post("", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    payload: CreateDatasetIn,
    principal: Principal,
    use_case: Annotated[CreateDatasetUseCase, Depends(get_create_dataset_use_case)],
) -> DatasetOut:
    dataset = await use_case.execute(org_id=org_id_of(principal), name=payload.name)
    return DatasetOut.from_domain(dataset)


@router.post(
    "/{dataset_id}/items:bulk", response_model=ImportResultOut, status_code=status.HTTP_201_CREATED
)
async def bulk_import_items(
    dataset_id: UUID,
    payload: BulkImportIn,
    principal: Principal,
    use_case: Annotated[ImportItemsUseCase, Depends(get_import_items_use_case)],
) -> ImportResultOut:
    result = await use_case.execute(
        org_id=org_id_of(principal),
        dataset_id=dataset_id,
        items=[item.to_domain() for item in payload.items],
    )
    return ImportResultOut.from_domain(result)


@router.get("/{dataset_id}", response_model=DatasetOut)
async def get_dataset(
    dataset_id: UUID,
    principal: Principal,
    use_case: Annotated[GetDatasetUseCase, Depends(get_get_dataset_use_case)],
) -> DatasetOut:
    dataset = await use_case.execute(org_id=org_id_of(principal), dataset_id=dataset_id)
    return DatasetOut.from_domain(dataset)


@router.get("/{dataset_id}/items", response_model=list[DatasetItemOut])
async def list_items(
    dataset_id: UUID,
    principal: Principal,
    use_case: Annotated[ListItemsUseCase, Depends(get_list_items_use_case)],
    version: int | None = Query(default=None, ge=1),
) -> list[DatasetItemOut]:
    items = await use_case.execute(org_id=org_id_of(principal), dataset_id=dataset_id, version=version)
    return [DatasetItemOut.from_domain(item) for item in items]
