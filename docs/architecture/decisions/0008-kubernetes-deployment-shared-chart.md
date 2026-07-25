# ADR-0008: One generic Helm chart, aliased 17 times, instead of 17 bespoke charts

## Status
Accepted — 2026-07-25 (Week 16)

## Context
By Week 16 the platform is 14 FastAPI services plus 3 Celery workers that
share an image with their FastAPI sibling (evaluation-engine,
report-generator, notification-service) — 17 deployable units in total.
Every one of them is a stateless container: a Deployment, sometimes a
Service, sometimes an `alembic upgrade head` step before it starts,
configured entirely by environment variables. Writing 17 near-identical
charts would mean 17 copies of the same Deployment/Service/Secret
boilerplate to keep in sync by hand.

## Decision
**One generic chart, `infra/k8s/helm/service-chart/`,** parameterized by
`image`, `command` (override, for the 3 workers), `service.enabled`,
`migrate.enabled`, `env`, and `envSecret`. An umbrella chart,
`infra/k8s/helm/platform/`, declares it as a dependency 17 times using
Helm's `alias:` mechanism — one alias per deployable unit — with all 17
configured in one `values.yaml`.

**Every alias sets `fullnameOverride`** to the same short name
`docker-compose.yml` already uses for that service (`gateway`, `auth`,
…). Helm's alias mechanism scopes *values* per alias but doesn't rename
the resources a subchart creates by itself — without this, all 17
instances would render as `<release>-service-chart` and collide. Setting
it explicitly means the in-cluster Service DNS name and the
docker-compose hostname are the same string, so every `*_URL` value in
`platform/values.yaml` is copy-paste identical to its docker-compose
counterpart.

**No Postgres or Redis dependency.** Real deployments typically manage
stateful databases separately from application charts — a cloud
provider's managed instance, a platform team's own operator, or (for a
local kind/minikube cluster) a separately-installed chart. Every
`*_DATABASE_URL`/`*_REDIS_URL` is a value the operator supplies (see
`platform/values-secrets.example.yaml`), pointed at whatever's actually
been provisioned. This also means the chart needs no external Helm
repository to install — `helm dependency update` only resolves local
`file://../service-chart` references, entirely offline (verified: `helm
lint` and `helm template` both pass, rendering 17 Deployments, 14
Services, and 16 Secrets with no name collisions — see
`infra/k8s/helm/README.md`).

## Consequences
- A real change to *how* one service is deployed (a new probe, a new
  volume mount, autoscaling) is a change to `service-chart`'s templates
  — applied to all 17 at once, correctly, by construction. A change that
  should apply to only *one* service (say, a sidecar only Gateway needs)
  doesn't fit this model cleanly yet; the generic chart would need a new
  opt-in value for it, which is a reasonable, contained follow-up rather
  than something the original design needs to anticipate now.
- The `values-secrets.example.yaml` split (checked in, placeholders only)
  vs. `values-secrets.yaml` (real values, gitignored) mirrors the
  `.env.example` vs. `.env` pattern every service already uses — same
  reasoning, same place secrets live.
- Not yet applied to a real cluster — this repo's sandbox has no cluster
  to apply it to (see `infra/k8s/helm/README.md`'s "Validated so far").
  `helm template`'s output is well-formed and structurally correct; a
  real `kubectl apply` (or `helm install --dry-run=server` against a live
  API server) is the next real check before a production rollout.
