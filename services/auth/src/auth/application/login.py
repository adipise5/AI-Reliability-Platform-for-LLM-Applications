"""Use case: exchange email + password for a session token (JWT)."""

from __future__ import annotations

from auth.domain.errors import InvalidCredentialsError
from auth.domain.ports import PasswordHasher, TokenIssuer, UserRepository


class LoginUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
        token_issuer: TokenIssuer,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._token_issuer = token_issuer

    async def execute(self, *, email: str, password: str) -> str:
        user = await self._user_repo.get_by_email(email)
        if user is None or not self._password_hasher.verify(password, user.password_hash):
            # Deliberately the same error for "no such user" and "wrong
            # password" — distinguishing them lets an attacker enumerate
            # registered emails.
            raise InvalidCredentialsError()
        return self._token_issuer.issue(user)
