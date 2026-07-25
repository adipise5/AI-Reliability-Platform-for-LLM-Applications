from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from auth.api.deps import SettingsDep, get_introspect_use_case, get_login_use_case
from auth.api.schemas import IntrospectIn, IntrospectOut, LoginIn, LoginOut
from auth.application.introspect import IntrospectUseCase
from auth.application.login import LoginUseCase

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginOut)
async def login(
    payload: LoginIn,
    use_case: Annotated[LoginUseCase, Depends(get_login_use_case)],
    settings: SettingsDep,
) -> LoginOut:
    token = await use_case.execute(email=payload.email, password=payload.password)
    return LoginOut(access_token=token, expires_in=settings.jwt_ttl_seconds)


@router.post("/introspect", response_model=IntrospectOut)
async def introspect(
    payload: IntrospectIn,
    use_case: Annotated[IntrospectUseCase, Depends(get_introspect_use_case)],
) -> IntrospectOut:
    principal = await use_case.execute(payload.credential)
    return IntrospectOut.from_domain(principal)
