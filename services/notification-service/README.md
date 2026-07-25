# Notification Service

Week 12 service. Org-scoped notification channels (Slack, email, generic
webhook) and the notifications sent through them — delivered
asynchronously via Celery, the same execution pattern as the Evaluation
Engine (Week 6) and the Report Generator (Week 11).

## What makes this service different from every other cross-service reader

Every other async worker in this project (the Evaluation Engine, the
Report Generator) forwards the caller's bearer token so the worker can
call *another ARP service* on the caller's behalf. This service never
does that: a channel's `target` is an external destination — a Slack
incoming-webhook URL, an email address, an arbitrary webhook URL — so
there's no ARP credential to forward, only delivery credentials this
service already owns (SMTP settings) or none at all (a webhook URL *is*
the credential). That's also why the service catalog lists its
dependency as "none": it never calls another bounded context.

## What this service owns

- `NotificationChannel` (`notifications.channels` — org-scoped delivery
  config: type, display name, target, enabled flag).
- `Notification` (`notifications.notifications` — one send request:
  subject, body, delivery status, and an error message if delivery
  failed).

## Delivery

Three senders, chosen by `ChannelType`:

- **Slack** — POSTs `{"text": ...}` to the channel's incoming-webhook URL.
- **Webhook** — POSTs `{"subject": ..., "body": ...}` to an arbitrary URL.
- **Email** — sent via `smtplib` against a configured SMTP relay (defaults
  point at a local dev relay like MailHog; there's no real mail provider
  this self-hosted platform can assume). `smtplib` is blocking, but this
  runs inside a Celery task already dedicated to one delivery at a time,
  so there's no event loop being blocked out from under other work.

Sending a notification validates the channel exists, belongs to the
caller's org, and is enabled *before* enqueueing — unlike the Evaluation
Engine or Report Generator's triggers, which skip that kind of check
specifically to avoid a network call to another service on every
request. There's no such call here, so the check is nearly free.

## Layering

```
src/notification_service/
├── domain/           NotificationChannel, Notification, errors, ports
├── application/       CreateChannelUseCase, ListChannelsUseCase, GetChannelUseCase,
│                      DeleteChannelUseCase, SendNotificationUseCase,
│                      DeliverNotificationUseCase, GetNotificationUseCase,
│                      ListNotificationsUseCase
├── infrastructure/     Slack/webhook/email senders, SQLAlchemy repositories,
│                       Celery worker + task queue, config
└── api/                FastAPI app, routers, schemas, DI wiring
```

## Endpoints

| Method & path | Auth | Description |
|---|---|---|
| `GET /healthz` | none | Liveness check |
| `POST /api/v1/channels` | bearer | Register a channel |
| `GET /api/v1/channels` | bearer | List this org's channels |
| `GET /api/v1/channels/{id}` | bearer | Channel metadata |
| `DELETE /api/v1/channels/{id}` | bearer | Remove a channel |
| `POST /api/v1/notifications` | bearer | Send a notification through a channel; returns immediately with status `pending` |
| `GET /api/v1/notifications?channel_id=` | bearer | List notifications for this org, most recent first |
| `GET /api/v1/notifications/{id}` | bearer | Notification metadata (status, error, timestamps) |

## Running locally

```bash
cd services/notification-service
python -m venv .venv && source .venv/bin/activate
pip install -e ../../libs/auth-client
pip install -e ".[dev]"
cp .env.example .env

alembic upgrade head
uvicorn notification_service.api.main:app --reload --port 8011

# in a second terminal, the worker that actually delivers notifications:
celery -A notification_service.infrastructure.worker worker -Q q.notification --loglevel=info
```

## Tests

```bash
pytest
```

- `tests/unit/` — every use case against fakes for both repositories and
  the sender registry; the Slack and webhook senders tested directly with
  respx; the SMTP email sender tested against a stubbed `smtplib.SMTP`.
- `tests/integration/test_channels_api.py`,
  `test_notifications_api.py` — the FastAPI app end-to-end.
- `tests/integration/test_repositories.py` — the real SQLAlchemy
  repositories against SQLite.

## Docker

Build context is the **repo root** (this service depends on
`libs/auth-client`). See `infra/docker-compose.yml`.
