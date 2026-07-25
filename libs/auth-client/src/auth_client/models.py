from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IntrospectionResult:
    """What the Authentication Service told us about a credential."""

    subject: str
    org_id: str
    scopes: frozenset[str]

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes
