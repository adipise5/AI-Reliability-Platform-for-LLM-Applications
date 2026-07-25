from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from auth.domain.errors import InvalidTokenError
from auth.infrastructure.security.jwt_token_issuer import JwtTokenIssuer


def test_verify_round_trips_an_issued_token(sample_owner):
    issuer = JwtTokenIssuer("test-secret-that-is-at-least-32-bytes-long")

    token = issuer.issue(sample_owner)
    principal = issuer.verify(token)

    assert principal.subject == f"user:{sample_owner.id}"
    assert principal.org_id == sample_owner.org_id
    assert principal.scopes == sample_owner.scopes


def test_verify_rejects_a_token_signed_with_a_different_secret(sample_owner):
    issuer_a = JwtTokenIssuer("secret-a-that-is-at-least-32-bytes-long")
    issuer_b = JwtTokenIssuer("secret-b-that-is-at-least-32-bytes-long")
    token = issuer_a.issue(sample_owner)

    with pytest.raises(InvalidTokenError):
        issuer_b.verify(token)


def test_verify_rejects_an_expired_token(sample_owner):
    secret = "test-secret-that-is-at-least-32-bytes-long"
    issuer = JwtTokenIssuer(secret)
    expired_payload = {
        "sub": f"user:{sample_owner.id}",
        "org_id": str(sample_owner.org_id),
        "scopes": sorted(sample_owner.scopes),
        "iat": datetime.now(UTC) - timedelta(hours=2),
        "exp": datetime.now(UTC) - timedelta(hours=1),
    }
    expired_token = jwt.encode(expired_payload, secret, algorithm="HS256")

    with pytest.raises(InvalidTokenError):
        issuer.verify(expired_token)


def test_verify_rejects_garbage_input():
    issuer = JwtTokenIssuer("test-secret-that-is-at-least-32-bytes-long")

    with pytest.raises(InvalidTokenError):
        issuer.verify("not-a-jwt-at-all")
