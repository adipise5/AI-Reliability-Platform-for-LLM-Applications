"""Week 1 AuthPort adapter — see ADR-0003.

Validates the bearer credential against a fixed set of keys from
configuration. Selected instead of ``RemoteAuthServiceAdapter`` whenever
`GATEWAY_STATIC_API_KEYS` is set — a dev/test convenience, not the
production path.
"""

from __future__ import annotations

from gateway.domain.entities import AuthContext
from gateway.domain.errors import AuthenticationError
from gateway.domain.ports import AuthPort

# Static keys have no real org concept — see ADR-0006. Fine for local,
# single-tenant use; every usage/cost record from this adapter is
# attributed here, which is exactly wrong for anything beyond that.
_STATIC_DEV_ORG_ID = "static-dev-org"


class StaticAPIKeyAuthAdapter(AuthPort):
    def __init__(self, valid_keys: frozenset[str]) -> None:
        self._valid_keys = valid_keys

    async def authenticate(self, credential: str) -> AuthContext:
        if not credential or credential not in self._valid_keys:
            raise AuthenticationError("unrecognized API key")
        return AuthContext(
            subject=f"static-key:{credential[:8]}",
            org_id=_STATIC_DEV_ORG_ID,
            scopes=frozenset({"chat:write"}),
        )
