"""API key secret hashing — plain SHA-256, not bcrypt.

Unlike passwords, API key secrets are 256 bits of `secrets.token_urlsafe`
output: high-entropy by construction, so a slow, salted KDF buys nothing
here and would only slow down every gateway request's auth check.
"""

from __future__ import annotations

import hashlib
import hmac


class Sha256ApiKeySecretHasher:
    def hash(self, secret: str) -> str:
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()

    def verify(self, secret: str, secret_hash: str) -> bool:
        return hmac.compare_digest(self.hash(secret), secret_hash)
