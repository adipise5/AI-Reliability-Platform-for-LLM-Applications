"""Domain-level errors.

The API layer maps these to HTTP responses (see api/main.py exception
handlers). Provider adapters must catch their SDK-specific exceptions and
re-raise as one of these so the rest of the system never depends on a
provider SDK's exception types.
"""

from __future__ import annotations


class GatewayError(Exception):
    """Base class for all domain errors raised by the gateway."""


class UnsupportedModelError(GatewayError):
    def __init__(self, model: str) -> None:
        self.model = model
        super().__init__(f"no provider registered for model {model!r}")


class AuthenticationError(GatewayError):
    def __init__(self, reason: str = "invalid or missing credentials") -> None:
        super().__init__(reason)


class AuthServiceUnavailableError(GatewayError):
    """The Authentication Service couldn't be reached — distinct from
    `AuthenticationError`: the credential may well be valid, the dependency
    is just down. Callers get a 503, not a 401 — see ADR-0003's Week 2
    update."""

    def __init__(self, reason: str = "authentication service unavailable") -> None:
        super().__init__(reason)


class ProviderRequestError(GatewayError):
    """A provider rejected or failed to service a request.

    ``retryable`` distinguishes transient failures (rate limits, timeouts)
    from permanent ones (bad request, invalid model) so callers can decide
    whether to retry without needing to know the underlying provider.
    """

    def __init__(self, provider: str, message: str, *, retryable: bool = False) -> None:
        self.provider = provider
        self.retryable = retryable
        super().__init__(f"[{provider}] {message}")
