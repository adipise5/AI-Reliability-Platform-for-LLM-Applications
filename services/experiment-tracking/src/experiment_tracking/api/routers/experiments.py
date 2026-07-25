from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, status

from experiment_tracking.api.deps import (
    get_add_run_use_case,
    get_bearer_credential,
    get_compare_experiment_use_case,
    get_create_experiment_use_case,
    get_get_experiment_use_case,
    org_id_of,
    require_principal,
)
from experiment_tracking.api.schemas import (
    AddRunIn,
    CreateExperimentIn,
    ExperimentComparisonOut,
    ExperimentOut,
    RemoteEvalRunSummaryOut,
)
from experiment_tracking.application.add_run import AddRunUseCase
from experiment_tracking.application.compare_experiment import CompareExperimentUseCase
from experiment_tracking.application.create_experiment import CreateExperimentUseCase
from experiment_tracking.application.get_experiment import GetExperimentUseCase

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.post("", response_model=ExperimentOut, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    payload: CreateExperimentIn,
    principal: Principal,
    use_case: Annotated[CreateExperimentUseCase, Depends(get_create_experiment_use_case)],
) -> ExperimentOut:
    experiment = await use_case.execute(
        org_id=org_id_of(principal), name=payload.name, description=payload.description
    )
    return ExperimentOut.from_domain(experiment)


@router.post("/{experiment_id}/runs", response_model=ExperimentOut, status_code=status.HTTP_201_CREATED)
async def add_run(
    experiment_id: UUID,
    payload: AddRunIn,
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[AddRunUseCase, Depends(get_add_run_use_case)],
) -> ExperimentOut:
    experiment = await use_case.execute(
        org_id=org_id_of(principal),
        experiment_id=experiment_id,
        run_id=payload.run_id,
        credential=credential,
    )
    return ExperimentOut.from_domain(experiment)


@router.get("/{experiment_id}", response_model=ExperimentOut)
async def get_experiment(
    experiment_id: UUID,
    principal: Principal,
    use_case: Annotated[GetExperimentUseCase, Depends(get_get_experiment_use_case)],
) -> ExperimentOut:
    experiment = await use_case.execute(org_id=org_id_of(principal), experiment_id=experiment_id)
    return ExperimentOut.from_domain(experiment)


@router.get("/{experiment_id}/comparison", response_model=ExperimentComparisonOut)
async def compare_experiment(
    experiment_id: UUID,
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[CompareExperimentUseCase, Depends(get_compare_experiment_use_case)],
) -> ExperimentComparisonOut:
    experiment, runs = await use_case.execute(
        org_id=org_id_of(principal), experiment_id=experiment_id, credential=credential
    )
    return ExperimentComparisonOut(
        experiment=ExperimentOut.from_domain(experiment),
        runs=[RemoteEvalRunSummaryOut.from_domain(r) for r in runs],
    )
