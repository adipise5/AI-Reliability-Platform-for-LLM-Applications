"""Ports: interfaces the application layer depends on.

Structural (`typing.Protocol`) rather than ABCs — see gateway's
domain/ports.py for the same rationale.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from auth.domain.entities import ApiKey, Org, Principal, User


class OrgRepository(Protocol):
    async def create(self, org: Org) -> None: ...

    async def get_by_id(self, org_id: UUID) -> Org | None: ...


class UserRepository(Protocol):
    async def create(self, user: User) -> None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def get_by_id(self, user_id: UUID) -> User | None: ...


class ApiKeyRepository(Protocol):
    async def create(self, api_key: ApiKey) -> None: ...

    async def get_by_prefix(self, prefix: str) -> ApiKey | None: ...

    async def get_by_id(self, key_id: UUID) -> ApiKey | None: ...

    async def revoke(self, key_id: UUID) -> None: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...


class ApiKeySecretHasher(Protocol):
    def hash(self, secret: str) -> str: ...

    def verify(self, secret: str, secret_hash: str) -> bool: ...


class TokenIssuer(Protocol):
    def issue(self, user: User) -> str: ...

    def verify(self, token: str) -> Principal:
        """Raises `auth.domain.errors.InvalidTokenError` on any failure —
        bad signature, expired, or malformed."""
        ...
