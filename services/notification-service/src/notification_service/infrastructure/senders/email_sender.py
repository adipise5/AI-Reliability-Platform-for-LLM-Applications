"""Delivers via SMTP — `channel.target` is the recipient address.

`smtplib` is blocking; there's no maintained async SMTP client in the
standard library, and pulling in `aiosmtplib` for one call site isn't
worth it at this scale. This runs inside a Celery task already dedicated
to one delivery at a time, so blocking the event loop briefly here (the
task's only coroutine) costs nothing a thread pool would meaningfully
improve.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from notification_service.domain.entities import ChannelType, Notification, NotificationChannel
from notification_service.domain.errors import DeliveryError


class SmtpEmailSender:
    channel_type = ChannelType.EMAIL

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        use_tls: bool,
        from_address: str,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._from_address = from_address

    async def send(self, channel: NotificationChannel, notification: Notification) -> None:
        message = EmailMessage()
        message["From"] = self._from_address
        message["To"] = channel.target
        message["Subject"] = notification.subject
        message.set_content(notification.body)

        try:
            with smtplib.SMTP(self._host, self._port, timeout=15) as smtp:
                if self._use_tls:
                    smtp.starttls()
                if self._username:
                    smtp.login(self._username, self._password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            raise DeliveryError(self.channel_type.value, str(exc)) from exc
