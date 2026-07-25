"""SQLAlchemy implementations of the repository ports.

Each method commits its own unit of work — simple and correct for the
single-write-per-request shape every use case here has today. A future
multi-step use case that needs one transaction across repositories would
take an `AsyncSession` directly instead; not needed yet.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.domain.entities import ApiKey, Org, Role, User
from auth.infrastructure.models import ApiKeyModel, OrgModel, UserModel


class SqlAlchemyOrgRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, org: Org) -> None:
        self._session.add(OrgModel(id=org.id, name=org.name, created_at=org.created_at))
        await self._session.commit()

    async def get_by_id(self, org_id: UUID) -> Org | None:
        model = await self._session.get(OrgModel, org_id)
        return _to_domain_org(model) if model else None


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user: User) -> None:
        self._session.add(
            UserModel(
                id=user.id,
                org_id=user.org_id,
                email=user.email,
                password_hash=user.password_hash,
                role=user.role.value,
                created_at=user.created_at,
            )
        )
        await self._session.commit()

    async def get_by_email(self, email: str) -> User | None:
        model = await self._session.scalar(select(UserModel).where(UserModel.email == email))
        return _to_domain_user(model) if model else None

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return _to_domain_user(model) if model else None


class SqlAlchemyApiKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, api_key: ApiKey) -> None:
        self._session.add(
            ApiKeyModel(
                id=api_key.id,
                org_id=api_key.org_id,
                name=api_key.name,
                prefix=api_key.prefix,
                secret_hash=api_key.secret_hash,
                scopes=sorted(api_key.scopes),
                created_at=api_key.created_at,
                revoked_at=api_key.revoked_at,
            )
        )
        await self._session.commit()

    async def get_by_prefix(self, prefix: str) -> ApiKey | None:
        model = await self._session.scalar(select(ApiKeyModel).where(ApiKeyModel.prefix == prefix))
        return _to_domain_api_key(model) if model else None

    async def get_by_id(self, key_id: UUID) -> ApiKey | None:
        model = await self._session.get(ApiKeyModel, key_id)
        return _to_domain_api_key(model) if model else None

    async def revoke(self, key_id: UUID) -> None:
        model = await self._session.get(ApiKeyModel, key_id)
        if model is not None:
            model.revoked_at = datetime.now(UTC)
            await self._session.commit()


def _to_domain_org(model: OrgModel) -> Org:
    return Org(id=model.id, name=model.name, created_at=model.created_at)


def _to_domain_user(model: UserModel) -> User:
    return User(
        id=model.id,
        org_id=model.org_id,
        email=model.email,
        password_hash=model.password_hash,
        role=Role(model.role),
        created_at=model.created_at,
    )


def _to_domain_api_key(model: ApiKeyModel) -> ApiKey:
    return ApiKey(
        id=model.id,
        org_id=model.org_id,
        name=model.name,
        prefix=model.prefix,
        secret_hash=model.secret_hash,
        scopes=frozenset(model.scopes),
        created_at=model.created_at,
        revoked_at=model.revoked_at,
    )
