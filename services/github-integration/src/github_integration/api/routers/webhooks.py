"""No `require_principal` here — GitHub calls this endpoint directly with
no bearer token; the HMAC signature over the raw payload is the only
authentication (see `domain/webhook_signature.py`)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status

from github_integration.api.deps import get_handle_webhook_use_case
from github_integration.api.schemas import CheckRunOut
from github_integration.application.handle_webhook import HandleWebhookUseCase

router = APIRouter(prefix="/webhooks/github", tags=["webhooks"])


@router.post("/{org_id}", status_code=status.HTTP_200_OK)
async def receive_webhook(
    org_id: UUID,
    request: Request,
    use_case: Annotated[HandleWebhookUseCase, Depends(get_handle_webhook_use_case)],
    x_github_event: Annotated[str | None, Header()] = None,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
) -> CheckRunOut | dict[str, str]:
    payload_bytes = await request.body()
    check = await use_case.execute(
        org_id=org_id,
        event_type=x_github_event or "",
        payload_bytes=payload_bytes,
        signature_header=x_hub_signature_256,
    )
    if check is None:
        return {"status": "ignored"}
    return CheckRunOut.from_domain(check)
