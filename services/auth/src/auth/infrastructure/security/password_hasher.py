"""User password hashing — bcrypt, chosen over a fast general-purpose hash
because passwords (unlike API key secrets) are low-entropy and must resist
offline brute force."""

from __future__ import annotations

import bcrypt


class BcryptPasswordHasher:
    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            # Malformed stored hash (shouldn't happen outside test fixtures
            # poking bad data in) — treat as "does not match", not a crash.
            return False
