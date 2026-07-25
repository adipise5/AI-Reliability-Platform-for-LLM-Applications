from __future__ import annotations

import pytest

from auth.application.register_org import RegisterOrgUseCase
from auth.domain.entities import Role
from auth.domain.errors import EmailAlreadyRegisteredError
from tests.unit.conftest import FakeOrgRepository, FakePasswordHasher, FakeUserRepository


async def test_execute_creates_org_and_owner():
    org_repo = FakeOrgRepository()
    user_repo = FakeUserRepository()
    use_case = RegisterOrgUseCase(org_repo, user_repo, FakePasswordHasher())

    org, owner = await use_case.execute(
        org_name="Acme", owner_email="owner@acme.example.com", owner_password="hunter22"
    )

    assert org_repo.orgs[org.id] is org
    assert user_repo.users[owner.id] is owner
    assert owner.org_id == org.id
    assert owner.role == Role.OWNER
    assert owner.password_hash == "22retnuh"  # FakePasswordHasher reverses the string


async def test_execute_rejects_duplicate_email(sample_owner):
    user_repo = FakeUserRepository(seed=[sample_owner])
    use_case = RegisterOrgUseCase(FakeOrgRepository(), user_repo, FakePasswordHasher())

    with pytest.raises(EmailAlreadyRegisteredError):
        await use_case.execute(
            org_name="Other Co", owner_email=sample_owner.email, owner_password="whatever1"
        )
