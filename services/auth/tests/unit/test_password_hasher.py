from __future__ import annotations

from auth.infrastructure.security.password_hasher import BcryptPasswordHasher


def test_verify_accepts_the_correct_password():
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash("correct-horse-battery-staple")

    assert hasher.verify("correct-horse-battery-staple", hashed)


def test_verify_rejects_the_wrong_password():
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash("correct-horse-battery-staple")

    assert not hasher.verify("wrong-password", hashed)


def test_verify_rejects_a_malformed_stored_hash():
    hasher = BcryptPasswordHasher()

    assert not hasher.verify("anything", "not-a-real-bcrypt-hash")


def test_hash_is_salted_so_two_hashes_of_the_same_password_differ():
    hasher = BcryptPasswordHasher()

    assert hasher.hash("same-password") != hasher.hash("same-password")
