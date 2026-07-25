"""Domain-level errors. The API layer maps these to HTTP responses."""

from __future__ import annotations


class AuthDomainError(Exception):
    """Base class for all domain errors raised by the auth service."""


class EmailAlreadyRegisteredError(AuthDomainError):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"{email!r} is already registered")


class InvalidCredentialsError(AuthDomainError):
    def __init__(self, reason: str = "invalid email or password") -> None:
        super().__init__(reason)


class InvalidTokenError(AuthDomainError):
    def __init__(self, reason: str = "invalid, expired, or revoked credential") -> None:
        super().__init__(reason)


class InsufficientScopeError(AuthDomainError):
    def __init__(self, requested: frozenset[str], available: frozenset[str]) -> None:
        self.requested = requested
        self.available = available
        missing = requested - available
        super().__init__(f"requested scopes {sorted(missing)} exceed caller's own scopes")


class ApiKeyNotFoundError(AuthDomainError):
    def __init__(self, key_id: str) -> None:
        self.key_id = key_id
        super().__init__(f"no api key {key_id!r} in this org")
