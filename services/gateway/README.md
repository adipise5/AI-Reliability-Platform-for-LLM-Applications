# AI Gateway

Week 1 service (auth wiring updated in Week 2). A unified chat-completion API across Claude, GPT, Gemini,
and local Ollama models. Stateless — no database of its own; see
[`docs/architecture/overview.md`](../../docs/architecture/overview.md) for
where it sits in the overall system.

## Layering

```
src/gateway/
├── domain/           entities, errors, ports — no framework imports (ADR-0001)
├── application/      RouteChatUseCase, StreamChatUseCase
├── infrastructure/   provider adapters, config, auth adapter, no-op sinks
└── api/              FastAPI app, routers, request/response schemas, DI wiring
```

`api/deps.py` is the only module that wires concrete adapters to use cases.
Route handlers depend on use cases and `AuthContext`, never on a provider
SDK or `Settings` directly.

## Endpoints

| Method & path | Auth | Description |
|---|---|---|
| `GET /healthz` | none | Liveness check |
| `POST /api/v1/chat` | Bearer token | Single chat completion |
| `POST /api/v1/chat/stream` | Bearer token | Server-Sent Events stream of the same |

Model routing is prefix-based (`infrastructure/provider_registry.py`):
`claude*` → Anthropic, `gpt*`/`o1*`/`o3*` → OpenAI, `gemini*` → Gemini,
anything else → Ollama (local models have no consistent naming convention,
so "not a known hosted vendor" is the practical signal for "local").

## Auth (see ADR-0003)

Two `AuthPort` adapters exist, chosen by configuration in `api/deps.py`:

- `RemoteAuthServiceAdapter` (default) — calls the Authentication Service's
  `POST /api/v1/auth/introspect` via the shared `auth_client` library.
  Used whenever `GATEWAY_STATIC_API_KEYS` is unset — this is what
  `infra/docker-compose.yml` runs.
- `StaticAPIKeyAuthAdapter` (dev convenience) — any bearer token listed in
  `GATEWAY_STATIC_API_KEYS` (comma-separated) is accepted locally, with no
  Postgres or Auth Service required. Wins whenever it's set.

An unreachable Authentication Service surfaces as `503`, not `401` — see
the domain error `AuthServiceUnavailableError`.

## Running locally

```bash
cd services/gateway
python -m venv .venv && source .venv/bin/activate
pip install -e ../../libs/auth-client   # shared auth client — install first
pip install -e ".[dev]"
cp .env.example .env   # then fill in whichever provider keys you have

uvicorn gateway.api.main:app --reload
```

By default this talks to a real Authentication Service at
`GATEWAY_AUTH_SERVICE_URL` (see `infra/docker-compose.yml` to run one). For
a Gateway-only smoke test with no other services running, set
`GATEWAY_STATIC_API_KEYS=dev-local-key` in `.env` instead.

At least one provider must be configured to be useful: set
`GATEWAY_OLLAMA_BASE_URL` to a running local Ollama daemon, and/or an API
key for Anthropic/OpenAI/Gemini. Providers without a configured key are
simply absent from the registry — requests for their models fail with a
`400 unsupported_model` rather than a startup error.

```bash
curl -s http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer dev-local-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.1", "messages": [{"role": "user", "content": "hi"}]}'
```

## Tests

```bash
pytest
```

- `tests/unit/` — use cases and infrastructure logic against fakes; no
  network, no real provider SDKs invoked.
- `tests/integration/` — the FastAPI app end-to-end via `TestClient`, with
  provider/auth dependencies overridden so no real credentials are needed.

## Docker

```bash
docker build -t arp-gateway .
docker run -p 8000:8000 --env-file .env arp-gateway
```

Or via the repo-wide `infra/docker-compose.yml`.
