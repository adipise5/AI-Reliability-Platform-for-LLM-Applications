"""Use case: register a new org together with its first (owner) user."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from auth.domain.entities import Org, Role, User
from auth.domain.errors import EmailAlreadyRegisteredError
from auth.domain.ports import OrgRepository, PasswordHasher, UserRepository


class RegisterOrgUseCase:
    def __init__(
        self,
        org_repo: OrgRepository,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._org_repo = org_repo
        self._user_repo = user_repo
        self._password_hasher = password_hasher

    async def execute(self, *, org_name: str, owner_email: str, owner_password: str) -> tuple[Org, User]:
        if await self._user_repo.get_by_email(owner_email) is not None:
            raise EmailAlreadyRegisteredError(owner_email)

        now = datetime.now(UTC)
        org = Org(id=uuid4(), name=org_name, created_at=now)
        owner = User(
            id=uuid4(),
            org_id=org.id,
            email=owner_email,
            password_hash=self._password_hasher.hash(owner_password),
            role=Role.OWNER,
            created_at=now,
        )
        await self._org_repo.create(org)
        await self._user_repo.create(owner)
        return org, owner
