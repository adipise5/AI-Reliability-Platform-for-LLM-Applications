from __future__ import annotations

from dataclasses import replace

import pytest

from auth.application.login import LoginUseCase
from auth.domain.errors import InvalidCredentialsError
from tests.unit.conftest import FakePasswordHasher, FakeTokenIssuer, FakeUserRepository


async def test_execute_returns_token_on_valid_credentials(sample_owner):
    hasher = FakePasswordHasher()
    user = replace(sample_owner, password_hash=hasher.hash("correct-horse"))
    user_repo = FakeUserRepository(seed=[user])
    issuer = FakeTokenIssuer()
    use_case = LoginUseCase(user_repo, hasher, issuer)

    token = await use_case.execute(email=user.email, password="correct-horse")

    assert issuer.issued[token] is user


async def test_execute_rejects_unknown_email():
    use_case = LoginUseCase(FakeUserRepository(), FakePasswordHasher(), FakeTokenIssuer())

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(email="ghost@nowhere.example.com", password="whatever1")


async def test_execute_rejects_wrong_password(sample_owner):
    hasher = FakePasswordHasher()
    user = replace(sample_owner, password_hash=hasher.hash("correct-horse"))
    user_repo = FakeUserRepository(seed=[user])
    use_case = LoginUseCase(user_repo, hasher, FakeTokenIssuer())

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(email=user.email, password="wrong-password")
