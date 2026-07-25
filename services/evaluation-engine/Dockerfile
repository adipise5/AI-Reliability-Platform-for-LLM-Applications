# Build context is the repo root (see infra/docker-compose.yml) — this
# service depends on libs/auth-client, which a services/<name>-scoped
# context can't reach.
#
# One image, two roles: the default CMD runs the FastAPI app; the
# docker-compose worker service overrides `command:` to run the Celery
# worker instead (`celery -A evaluation_engine.infrastructure.worker worker`).
FROM python:3.12-slim AS base

WORKDIR /build

COPY libs/auth-client ./libs/auth-client
COPY services/evaluation-engine ./services/evaluation-engine

RUN pip install --no-cache-dir ./libs/auth-client ./services/evaluation-engine

WORKDIR /build/services/evaluation-engine

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

CMD ["sh", "-c", "alembic upgrade head && uvicorn evaluation_engine.api.main:app --host 0.0.0.0 --port 8000"]
