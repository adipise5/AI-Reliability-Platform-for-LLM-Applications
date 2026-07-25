from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, status

from notification_service.api.deps import (
    get_create_channel_use_case,
    get_delete_channel_use_case,
    get_get_channel_use_case,
    get_list_channels_use_case,
    org_id_of,
    require_principal,
)
from notification_service.api.schemas import ChannelOut, CreateChannelIn
from notification_service.application.create_channel import CreateChannelUseCase
from notification_service.application.delete_channel import DeleteChannelUseCase
from notification_service.application.get_channel import GetChannelUseCase
from notification_service.application.list_channels import ListChannelsUseCase

router = APIRouter(prefix="/api/v1/channels", tags=["channels"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.post("", response_model=ChannelOut, status_code=status.HTTP_201_CREATED)
async def create_channel(
    payload: CreateChannelIn,
    principal: Principal,
    use_case: Annotated[CreateChannelUseCase, Depends(get_create_channel_use_case)],
) -> ChannelOut:
    channel = await use_case.execute(
        org_id=org_id_of(principal),
        channel_type=payload.channel_type,
        name=payload.name,
        target=payload.target,
    )
    return ChannelOut.from_domain(channel)


@router.get("", response_model=list[ChannelOut])
async def list_channels(
    principal: Principal,
    use_case: Annotated[ListChannelsUseCase, Depends(get_list_channels_use_case)],
) -> list[ChannelOut]:
    channels = await use_case.execute(org_id=org_id_of(principal))
    return [ChannelOut.from_domain(c) for c in channels]


@router.get("/{channel_id}", response_model=ChannelOut)
async def get_channel(
    channel_id: UUID,
    principal: Principal,
    use_case: Annotated[GetChannelUseCase, Depends(get_get_channel_use_case)],
) -> ChannelOut:
    channel = await use_case.execute(org_id=org_id_of(principal), channel_id=channel_id)
    return ChannelOut.from_domain(channel)


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: UUID,
    principal: Principal,
    use_case: Annotated[DeleteChannelUseCase, Depends(get_delete_channel_use_case)],
) -> None:
    await use_case.execute(org_id=org_id_of(principal), channel_id=channel_id)
