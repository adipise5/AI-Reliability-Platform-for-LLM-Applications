"""Dependency wiring — see the gateway's api/deps.py for the rationale:
this is the one module allowed to know about concrete adapters."""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from auth.application.create_api_key import CreateApiKeyUseCase
from auth.application.introspect import IntrospectUseCase
from auth.application.login import LoginUseCase
from auth.application.register_org import RegisterOrgUseCase
from auth.application.revoke_api_key import RevokeApiKeyUseCase
from auth.domain.entities import Principal
from auth.domain.errors import InvalidTokenError
from auth.domain.ports import (
    ApiKeyRepository,
    ApiKeySecretHasher,
    OrgRepository,
    PasswordHasher,
    TokenIssuer,
    UserRepository,
)
from auth.infrastructure.config import Settings, get_settings
from auth.infrastructure.db import build_engine, build_session_factory
from auth.infrastructure.repositories import (
    SqlAlchemyApiKeyRepository,
    SqlAlchemyOrgRepository,
    SqlAlchemyUserRepository,
)
from auth.infrastructure.security.api_key_hasher import Sha256ApiKeySecretHasher
from auth.infrastructure.security.jwt_token_issuer import JwtTokenIssuer
from auth.infrastructure.security.password_hasher import BcryptPasswordHasher

_bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def _build_engine() -> AsyncEngine:
    return build_engine(get_settings().database_url)


@lru_cache
def _build_session_factory() -> async_sessionmaker[AsyncSession]:
    return build_session_factory(_build_engine())


async def get_session() -> AsyncIterator[AsyncSession]:
    async with _build_session_factory()() as session:
        yield session


def get_org_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> OrgRepository:
    return SqlAlchemyOrgRepository(session)


def get_user_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_api_key_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> ApiKeyRepository:
    return SqlAlchemyApiKeyRepository(session)


@lru_cache
def _password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


@lru_cache
def _secret_hasher() -> ApiKeySecretHasher:
    return Sha256ApiKeySecretHasher()


@lru_cache
def _token_issuer() -> TokenIssuer:
    settings = get_settings()
    return JwtTokenIssuer(
        settings.jwt_secret, algorithm=settings.jwt_algorithm, ttl_seconds=settings.jwt_ttl_seconds
    )


def get_register_org_use_case(
    org_repo: Annotated[OrgRepository, Depends(get_org_repo)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> RegisterOrgUseCase:
    return RegisterOrgUseCase(org_repo, user_repo, _password_hasher())


def get_login_use_case(
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> LoginUseCase:
    return LoginUseCase(user_repo, _password_hasher(), _token_issuer())


def get_introspect_use_case(
    api_key_repo: Annotated[ApiKeyRepository, Depends(get_api_key_repo)],
) -> IntrospectUseCase:
    return IntrospectUseCase(_token_issuer(), api_key_repo, _secret_hasher())


def get_create_api_key_use_case(
    api_key_repo: Annotated[ApiKeyRepository, Depends(get_api_key_repo)],
) -> CreateApiKeyUseCase:
    return CreateApiKeyUseCase(
        api_key_repo, _secret_hasher(), key_environment=get_settings().api_key_environment
    )


def get_revoke_api_key_use_case(
    api_key_repo: Annotated[ApiKeyRepository, Depends(get_api_key_repo)],
) -> RevokeApiKeyUseCase:
    return RevokeApiKeyUseCase(api_key_repo)


async def require_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> Principal:
    # Session-only, deliberately: this resolves a JWT and nothing else, so
    # an API key can never be used to mint or revoke other API keys.
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    try:
        return _token_issuer().verify(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


async def require_org_admin(principal: Annotated[Principal, Depends(require_user)]) -> Principal:
    if "org:admin" not in principal.scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="requires org:admin scope")
    return principal


def reset_cached_singletons() -> None:
    """Test-only hook — see the gateway's equivalent for why."""
    get_settings.cache_clear()
    _build_engine.cache_clear()
    _build_session_factory.cache_clear()
    _password_hasher.cache_clear()
    _secret_hasher.cache_clear()
    _token_issuer.cache_clear()


SettingsDep = Annotated[Settings, Depends(get_settings)]
