# Build context is the repo root (see infra/docker-compose.yml) — this
# service depends on libs/auth-client, which a services/<name>-scoped
# context can't reach.
FROM python:3.12-slim AS base

WORKDIR /build

COPY libs/auth-client ./libs/auth-client
COPY services/dashboard-backend ./services/dashboard-backend

RUN pip install --no-cache-dir ./libs/auth-client ./services/dashboard-backend

WORKDIR /build/services/dashboard-backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

# No `alembic upgrade head` step — this service has no database of its
# own (see infrastructure/config.py's docstring).
CMD ["uvicorn", "dashboard_backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
