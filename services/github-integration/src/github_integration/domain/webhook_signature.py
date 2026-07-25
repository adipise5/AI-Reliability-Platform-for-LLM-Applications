"""GitHub signs webhook deliveries with `X-Hub-Signature-256: sha256=<hex
hmac>` over the raw request body. Verifying it is pure stdlib logic with
no I/O, so it lives here as a plain function rather than behind a port —
there's nothing to fake, and the constant-time comparison is the entire
point of testing this in isolation."""

from __future__ import annotations

import hashlib
import hmac


def verify_signature(secret: str, payload: bytes, signature_header: str | None) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    provided = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, provided)
