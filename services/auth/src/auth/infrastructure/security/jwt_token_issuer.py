"""Session tokens — signed JWTs, HS256 by default.

A single shared secret (`AUTH_JWT_SECRET`) is enough while this service is
the only issuer and verifier; moving to per-org or asymmetric signing would
only matter once a second service needs to verify tokens without calling
back into this one, which nothing does today (everyone calls
`/api/v1/auth/introspect` instead — see ADR-0003).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from auth.domain.entities import Principal, User
from auth.domain.errors import InvalidTokenError


class JwtTokenIssuer:
    def __init__(self, secret: str, *, algorithm: str = "HS256", ttl_seconds: int = 3600) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._ttl_seconds = ttl_seconds

    def issue(self, user: User) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": f"user:{user.id}",
            "org_id": str(user.org_id),
            "scopes": sorted(user.scopes),
            "iat": now,
            "exp": now + timedelta(seconds=self._ttl_seconds),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def verify(self, token: str) -> Principal:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.PyJWTError as exc:
            raise InvalidTokenError(str(exc)) from exc

        try:
            return Principal(
                subject=payload["sub"],
                org_id=UUID(payload["org_id"]),
                scopes=frozenset(payload["scopes"]),
            )
        except (KeyError, ValueError) as exc:
            raise InvalidTokenError("malformed token payload") from exc
