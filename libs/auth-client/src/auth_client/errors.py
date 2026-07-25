from __future__ import annotations


class AuthClientError(Exception):
    """Base class for all errors raised by AuthServiceClient."""


class UnauthenticatedError(AuthClientError):
    """The Authentication Service rejected the credential outright."""


class AuthServiceUnavailableError(AuthClientError):
    """The Authentication Service could not be reached or errored (5xx).

    Callers should treat this differently from `UnauthenticatedError`: a
    down auth service is an operational problem, not proof the caller's
    credential is invalid.
    """
