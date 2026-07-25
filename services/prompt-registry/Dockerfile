# Build context is the repo root (see infra/docker-compose.yml) — this
# service depends on libs/auth-client, which a services/<name>-scoped
# context can't reach.
FROM python:3.12-slim AS base

WORKDIR /build

COPY libs/auth-client ./libs/auth-client
COPY services/prompt-registry ./services/prompt-registry

RUN pip install --no-cache-dir ./libs/auth-client ./services/prompt-registry

WORKDIR /build/services/prompt-registry

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

CMD ["sh", "-c", "alembic upgrade head && uvicorn prompt_registry.api.main:app --host 0.0.0.0 --port 8000"]
