# Kubernetes / Helm

Two charts:

- **`service-chart/`** — generic chart for one deployable unit (a FastAPI
  service, or a Celery worker sharing its sibling's image). Everything
  service-specific is a value: image, env, whether it exposes a port,
  whether it needs an `alembic upgrade head` init container, what command
  to run. See its own comments in `values.yaml` for the full list.
- **`platform/`** — the umbrella chart. Declares one aliased dependency
  on `service-chart` per deployable unit (17 total: 14 FastAPI services +
  3 Celery workers — evaluation-engine, report-generator, and
  notification-service each have one), and `values.yaml` configures all
  17 in one file, matching `infra/docker-compose.yml`'s service names and
  environment variables 1:1.

## Why there's no Postgres/Redis dependency here

Deliberately not bundled. In real deployments these are typically managed
separately from application charts — a cloud provider's managed Postgres/
Redis, a platform team's own Postgres operator, or (for a local kind/minikube
cluster) a separately-installed chart like Bitnami's. Point every
`*_DATABASE_URL`/`*_REDIS_URL` in `values-secrets.yaml` at whatever you've
provisioned. This also means this chart needs no external Helm repository
to install — `helm dependency update` only resolves local
`file://../service-chart` references, entirely offline.

## Why every alias sets `fullnameOverride`

Helm's dependency-alias mechanism scopes *values* per alias, but doesn't
rename the resources a subchart creates — every one of the 17 instances
would render as `<release>-service-chart` and collide. Each block in
`values.yaml` sets `fullnameOverride` to the same short name
`docker-compose.yml` uses for that service (`gateway`, `auth`, …), which
also means every `*_URL` in `values.yaml` is copy-paste identical to its
docker-compose counterpart — the in-cluster Service DNS name and the
docker-compose hostname are the same string.

## Building images

Each service's own `Dockerfile` already exists (see `services/<name>/Dockerfile`
and its repo-root build context requirement for anything depending on
`libs/auth-client`). Tag them to match `values.yaml`'s `image.repository`
(`arp-<service>`), e.g.:

```bash
docker build -f services/gateway/Dockerfile -t your-registry/arp-gateway:1.0.0 .
docker push your-registry/arp-gateway:1.0.0
```

Repeat per service, then override `image.repository`/`image.tag` (or set a
shared `global.imageRegistry` prefix at install time) to point at wherever
you pushed them.

## Installing

```bash
cd infra/k8s/helm/platform
helm dependency update .
cp values-secrets.example.yaml values-secrets.yaml   # fill in real values — gitignored
helm install arp . -f values-secrets.yaml
```

`helm template . -f values-secrets.yaml` renders everything locally without
touching a cluster — useful for reviewing what would be created, or diffing
against a previous release.

## Validated so far

`helm lint` and `helm template` (both charts) — 17 Deployments, 14 Services
(workers have none), 16 Secrets (every alias but `dashboard-backend`, which
has no database) all render as expected, with no name collisions and correct
per-alias `command`/`env`/`service.enabled` overrides. Not yet applied to a
real cluster — this repo sandbox has no cluster to apply it to. `kubectl
apply --dry-run=server` against a real API server is the next real check
before a production install.
