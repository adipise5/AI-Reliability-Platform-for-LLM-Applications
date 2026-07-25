from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from auth.domain.entities import ApiKey, Org, Principal, Role, User
from auth.domain.errors import InvalidTokenError


class FakeOrgRepository:
    def __init__(self) -> None:
        self.orgs: dict[UUID, Org] = {}

    async def create(self, org: Org) -> None:
        self.orgs[org.id] = org

    async def get_by_id(self, org_id: UUID) -> Org | None:
        return self.orgs.get(org_id)


class FakeUserRepository:
    def __init__(self, seed: list[User] | None = None) -> None:
        self.users: dict[UUID, User] = {u.id: u for u in (seed or [])}

    async def create(self, user: User) -> None:
        self.users[user.id] = user

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.users.values() if u.email == email), None)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.users.get(user_id)


class FakeApiKeyRepository:
    def __init__(self, seed: list[ApiKey] | None = None) -> None:
        self.keys: dict[UUID, ApiKey] = {k.id: k for k in (seed or [])}

    async def create(self, api_key: ApiKey) -> None:
        self.keys[api_key.id] = api_key

    async def get_by_prefix(self, prefix: str) -> ApiKey | None:
        return next((k for k in self.keys.values() if k.prefix == prefix), None)

    async def get_by_id(self, key_id: UUID) -> ApiKey | None:
        return self.keys.get(key_id)

    async def revoke(self, key_id: UUID) -> None:
        key = self.keys.get(key_id)
        if key is not None:
            self.keys[key_id] = ApiKey(
                id=key.id,
                org_id=key.org_id,
                name=key.name,
                prefix=key.prefix,
                secret_hash=key.secret_hash,
                scopes=key.scopes,
                created_at=key.created_at,
                revoked_at=datetime.now(UTC),
            )


class FakePasswordHasher:
    """Reverses the string instead of real hashing — fast and obviously
    not for production use, only for exercising use-case logic."""

    def hash(self, password: str) -> str:
        return password[::-1]

    def verify(self, password: str, password_hash: str) -> bool:
        return password[::-1] == password_hash


class FakeApiKeySecretHasher:
    def hash(self, secret: str) -> str:
        return secret[::-1]

    def verify(self, secret: str, secret_hash: str) -> bool:
        return secret[::-1] == secret_hash


class FakeTokenIssuer:
    def __init__(self) -> None:
        self.issued: dict[str, User] = {}

    def issue(self, user: User) -> str:
        token = f"fake-token:{user.id}"
        self.issued[token] = user
        return token

    def verify(self, token: str) -> Principal:
        user = self.issued.get(token)
        if user is None:
            raise InvalidTokenError("unknown fake token")
        return Principal(subject=f"user:{user.id}", org_id=user.org_id, scopes=user.scopes)


@pytest.fixture
def sample_org() -> Org:
    return Org(id=uuid4(), name="Acme", created_at=datetime.now(UTC))


@pytest.fixture
def sample_owner(sample_org: Org) -> User:
    return User(
        id=uuid4(),
        org_id=sample_org.id,
        email="owner@acme.example.com",
        password_hash="hashed",
        role=Role.OWNER,
        created_at=datetime.now(UTC),
    )
