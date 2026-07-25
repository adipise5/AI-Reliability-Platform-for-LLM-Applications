from __future__ import annotations

import smtplib
from unittest.mock import MagicMock

import pytest

from notification_service.domain.errors import DeliveryError
from notification_service.infrastructure.senders.email_sender import SmtpEmailSender
from tests.unit.conftest import make_channel, make_notification


def _fake_smtp_class(instance: MagicMock) -> MagicMock:
    factory = MagicMock(return_value=instance)
    instance.__enter__ = MagicMock(return_value=instance)
    instance.__exit__ = MagicMock(return_value=False)
    return factory


async def test_sends_via_smtp_with_tls_and_login(monkeypatch):
    smtp_instance = MagicMock()
    monkeypatch.setattr(
        "notification_service.infrastructure.senders.email_sender.smtplib.SMTP",
        _fake_smtp_class(smtp_instance),
    )
    sender = SmtpEmailSender(
        host="smtp.example.com",
        port=587,
        username="user",
        password="pw",
        use_tls=True,
        from_address="arp@example.com",
    )
    channel = make_channel(target="alerts@example.com")
    notification = make_notification(subject="s", body="b")

    await sender.send(channel, notification)

    smtp_instance.starttls.assert_called_once()
    smtp_instance.login.assert_called_once_with("user", "pw")
    smtp_instance.send_message.assert_called_once()
    sent_message = smtp_instance.send_message.call_args[0][0]
    assert sent_message["To"] == "alerts@example.com"
    assert sent_message["Subject"] == "s"


async def test_skips_login_when_no_username(monkeypatch):
    smtp_instance = MagicMock()
    monkeypatch.setattr(
        "notification_service.infrastructure.senders.email_sender.smtplib.SMTP",
        _fake_smtp_class(smtp_instance),
    )
    sender = SmtpEmailSender(
        host="localhost", port=1025, username="", password="", use_tls=False, from_address="a@b.com"
    )
    channel = make_channel(target="alerts@example.com")
    notification = make_notification()

    await sender.send(channel, notification)

    smtp_instance.starttls.assert_not_called()
    smtp_instance.login.assert_not_called()
    smtp_instance.send_message.assert_called_once()


async def test_raises_delivery_error_on_smtp_exception(monkeypatch):
    def _raise(*args: object, **kwargs: object) -> None:
        raise smtplib.SMTPConnectError(421, "unavailable")

    monkeypatch.setattr(
        "notification_service.infrastructure.senders.email_sender.smtplib.SMTP", _raise
    )
    sender = SmtpEmailSender(
        host="localhost", port=1025, username="", password="", use_tls=False, from_address="a@b.com"
    )
    channel = make_channel(target="alerts@example.com")
    notification = make_notification()

    with pytest.raises(DeliveryError):
        await sender.send(channel, notification)
