# GitHub Integration

Week 13 service. The CI-facing surface of the platform: receives GitHub
webhooks, creates and completes GitHub check runs, and posts PR comments —
the piece that turns Regression Detection's gate decisions (Week 10) into
something a pull request actually shows.

## The flow

1. A PR is opened or pushed to. GitHub sends a `pull_request` webhook to
   `POST /webhooks/github/{org_id}`. `HandleWebhookUseCase` verifies the
   HMAC signature, creates a GitHub check run in `queued` state for the
   PR's head commit, and records it locally as a `CheckRun`.
2. The repo's own CI workflow (not this service) triggers an eval run
   against the Evaluation Engine for whatever prompt changed, the same
   way it would outside CI.
3. Once that run completes, the workflow looks up the check id this
   service created — `GET /api/v1/checks?repo=&commit_sha=` — and calls
   `POST /api/v1/checks/{id}/complete` with the eval run's id.
   `CompleteCheckUseCase` asks Regression Detection for that run's gate
   decision, translates its verdict into a GitHub conclusion
   (`pass`→`success`, `fail`→`failure`, `needs_review`→`neutral`), and
   updates the check run on GitHub.
4. The workflow (or a person) can also call
   `POST /api/v1/checks/{id}/comment` to leave a PR comment — kept as a
   separate call since not every gate result needs a comment, only a
   check run.

## Why the webhook endpoint has no bearer auth

Every other endpoint here requires the normal `RequirePrincipal` bearer
token. The webhook endpoint doesn't — GitHub calls it directly with no
ARP credential at all. It's authenticated instead by verifying the
`X-Hub-Signature-256` HMAC header against a shared secret (see
`domain/webhook_signature.py`), the same authentication story every
webhook receiver in this ecosystem uses.

## A known simplification

Both the GitHub token (used to create/update check runs and post
comments) and the webhook secret are single, static, deployment-wide
values from config — there's no per-org GitHub App installation-token
exchange yet. That means every org in one deployment currently posts
through the same GitHub identity. Fine for a single-tenant self-hosted
install (the common case for this project); a real multi-tenant SaaS
deployment would need a GitHub App with per-installation tokens and a
per-org webhook secret, which is a reasonable follow-up, not something
this milestone needs.

## Layering

```
src/github_integration/
├── domain/           CheckRun, RemoteGateDecision, errors, ports, webhook_signature
├── application/       HandleWebhookUseCase, CompleteCheckUseCase, PostPrCommentUseCase,
│                      GetCheckUseCase, ListChecksUseCase
├── infrastructure/     HttpGitHubClient, HttpGateDecisionReader, SQLAlchemy repository, config
└── api/                FastAPI app, routers, schemas, DI wiring
```

## Endpoints

| Method & path | Auth | Description |
|---|---|---|
| `GET /healthz` | none | Liveness check |
| `POST /webhooks/github/{org_id}` | HMAC signature | GitHub's webhook delivery target |
| `GET /api/v1/checks?repo=&commit_sha=` | bearer | Find a check by repo + commit |
| `GET /api/v1/checks/{id}` | bearer | Check metadata |
| `POST /api/v1/checks/{id}/complete` | bearer | Gate an eval run and finish the check on GitHub |
| `POST /api/v1/checks/{id}/comment` | bearer | Post a PR comment |

## Running locally

```bash
cd services/github-integration
python -m venv .venv && source .venv/bin/activate
pip install -e ../../libs/auth-client
pip install -e ".[dev]"
cp .env.example .env

alembic upgrade head
uvicorn github_integration.api.main:app --reload --port 8012
```

## Tests

```bash
pytest
```

- `tests/unit/` — every use case against fakes for the repository,
  `GitHubClient`, and `GateDecisionReader`; the webhook signature
  verification tested directly (valid, missing, tampered, wrong-secret);
  both HTTP clients tested with respx.
- `tests/integration/test_webhooks_api.py`, `test_checks_api.py` — the
  FastAPI app end-to-end.
- `tests/integration/test_repositories.py` — the real SQLAlchemy
  repository against SQLite.

## Docker

Build context is the **repo root** (this service depends on
`libs/auth-client`). See `infra/docker-compose.yml`.
