from __future__ import annotations

from github_integration.domain.webhook_signature import verify_signature
from tests.unit.conftest import signed_payload


def test_valid_signature_verifies():
    body, signature = signed_payload("s3cr3t", {"a": 1})

    assert verify_signature("s3cr3t", body, signature) is True


def test_wrong_secret_fails():
    body, signature = signed_payload("s3cr3t", {"a": 1})

    assert verify_signature("wrong-secret", body, signature) is False


def test_tampered_payload_fails():
    body, signature = signed_payload("s3cr3t", {"a": 1})

    assert verify_signature("s3cr3t", body + b"tampered", signature) is False


def test_missing_signature_header_fails():
    body, _ = signed_payload("s3cr3t", {"a": 1})

    assert verify_signature("s3cr3t", body, None) is False


def test_wrong_prefix_fails():
    body, signature = signed_payload("s3cr3t", {"a": 1})
    bad_header = signature.replace("sha256=", "sha1=")

    assert verify_signature("s3cr3t", body, bad_header) is False
