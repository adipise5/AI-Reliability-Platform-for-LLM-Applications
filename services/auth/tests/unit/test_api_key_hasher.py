from __future__ import annotations

from auth.infrastructure.security.api_key_hasher import Sha256ApiKeySecretHasher


def test_verify_accepts_the_matching_secret():
    hasher = Sha256ApiKeySecretHasher()
    hashed = hasher.hash("arp_live_deadbeef.some-secret")

    assert hasher.verify("arp_live_deadbeef.some-secret", hashed)


def test_verify_rejects_a_different_secret():
    hasher = Sha256ApiKeySecretHasher()
    hashed = hasher.hash("arp_live_deadbeef.some-secret")

    assert not hasher.verify("arp_live_deadbeef.wrong-secret", hashed)


def test_hash_is_deterministic():
    hasher = Sha256ApiKeySecretHasher()

    assert hasher.hash("same-secret") == hasher.hash("same-secret")
