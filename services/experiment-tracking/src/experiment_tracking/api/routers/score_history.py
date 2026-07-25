from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, Query

from experiment_tracking.api.deps import get_bearer_credential, get_score_history_use_case, require_principal
from experiment_tracking.api.schemas import RemoteEvalRunSummaryOut
from experiment_tracking.application.get_score_history import GetScoreHistoryUseCase

router = APIRouter(prefix="/api/v1/score-history", tags=["score-history"])


@router.get("", response_model=list[RemoteEvalRunSummaryOut])
async def get_score_history(
    principal: Annotated[IntrospectionResult, Depends(require_principal)],
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[GetScoreHistoryUseCase, Depends(get_score_history_use_case)],
    prompt_id: UUID = Query(...),
) -> list[RemoteEvalRunSummaryOut]:
    del principal  # authentication only — the Evaluation Engine scopes by the forwarded credential
    runs = await use_case.execute(credential=credential, prompt_id=prompt_id)
    return [RemoteEvalRunSummaryOut.from_domain(r) for r in runs]
