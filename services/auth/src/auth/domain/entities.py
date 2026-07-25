"""Domain entities and value objects for the Authentication Service.

Nothing here imports FastAPI, SQLAlchemy, or a JWT/crypto library — see
ADR-0001. `uuid` and `datetime` are standard library, not frameworks.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


# The platform's RBAC model is deliberately flat for now: a fixed set of
# roles, each with a fixed scope set, rather than a configurable
# permissions matrix. `role_bindings` in the schema exists so a user's role
# can change or a user can be removed from an org without deleting their
# account — not to support per-user custom scopes yet.
ROLE_SCOPES: dict[Role, frozenset[str]] = {
    Role.OWNER: frozenset({"chat:write", "org:admin"}),
    Role.ADMIN: frozenset({"chat:write", "org:admin"}),
    Role.MEMBER: frozenset({"chat:write"}),
}


@dataclass(frozen=True, slots=True)
class Org:
    id: UUID
    name: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    org_id: UUID
    email: str
    password_hash: str
    role: Role
    created_at: datetime

    @property
    def scopes(self) -> frozenset[str]:
        return ROLE_SCOPES[self.role]


@dataclass(frozen=True, slots=True)
class ApiKey:
    id: UUID
    org_id: UUID
    name: str
    prefix: str
    secret_hash: str
    scopes: frozenset[str]
    created_at: datetime
    revoked_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None


@dataclass(frozen=True, slots=True)
class Principal:
    """What introspection resolves a credential to — a user session or an
    API key, uniformly, for whichever service is asking."""

    subject: str
    org_id: UUID
    scopes: frozenset[str]
