# Hallucination / Faithfulness Detection

Week 7 service. Checks whether an LLM response is *grounded* in a given
context (a RAG-retrieved passage, a source document, whatever the caller
supplies) using the same claim-extraction-then-verification technique
RAG-faithfulness evaluators like RAGAS use — not a novel invention, a
standard one implemented from scratch:

1. **Extract** the response into a list of atomic factual claims (a
   Gateway call).
2. **Verify** each claim against the context independently — `SUPPORTED`,
   `CONTRADICTED`, or `NOT_ENOUGH_INFO` — concurrently, since each is its
   own Gateway call.
3. **Score**: the fraction of claims marked `SUPPORTED`. `NOT_ENOUGH_INFO`
   counts against the score exactly like `CONTRADICTED` — "the context
   doesn't confirm this" isn't the same as "this is grounded," and
   scoring it as a wash would understate ungrounded-but-plausible-sounding
   responses.

## Layering

```
src/hallucination_detection/
├── domain/           FaithfulnessCheck, Claim, Verdict, errors, ports
├── application/      CheckFaithfulnessUseCase, GetCheckUseCase
├── infrastructure/    HttpGatewayClient, GatewayClaimExtractor, GatewayClaimVerifier,
│                      SQLAlchemy repository, config
└── api/               FastAPI app, routers, schemas, DI wiring
```

## Why synchronous, not async

The service catalog in `docs/architecture/overview.md` originally
categorized this service as async. In practice, its main consumer is the
Evaluation Engine's `faithfulness` scorer (see that service's
`infrastructure/scorers/`), which needs a score back within its per-item
loop — same shape as its existing `llm_judge` scorer calling the Gateway
directly. `POST /api/v1/faithfulness-checks` is a normal synchronous
REST call, exactly like the Gateway's own `/api/v1/chat`: slow because an
LLM is involved, not because of a queue.

## Endpoints

| Method & path | Auth | Description |
|---|---|---|
| `GET /healthz` | none | Liveness check |
| `POST /api/v1/faithfulness-checks` | bearer | Run a check; returns the full result immediately |
| `GET /api/v1/faithfulness-checks/{id}` | bearer | Re-fetch a past check |

The bearer credential authenticates the caller *and* is forwarded to the
Gateway for the extraction/verification calls — same pattern, and same
JWT-TTL caveat, as the Evaluation Engine (see ADR-0005).

## Running locally

```bash
cd services/hallucination-detection
python -m venv .venv && source .venv/bin/activate
pip install -e ../../libs/auth-client
pip install -e ".[dev]"
cp .env.example .env

alembic upgrade head
uvicorn hallucination_detection.api.main:app --reload --port 8006
```

## Tests

```bash
pytest
```

- `tests/unit/` — `CheckFaithfulnessUseCase` against fakes for the
  extractor, verifier, and repository; the claim-parsing logic in
  `GatewayClaimExtractor`/`GatewayClaimVerifier` tested directly against
  known model output shapes (including malformed ones).
- `tests/integration/test_checks_api.py` — the FastAPI app end-to-end.
- `tests/integration/test_repositories.py` — the real SQLAlchemy
  repository against SQLite.

## Docker

Build context is the **repo root** (this service depends on
`libs/auth-client`). See `infra/docker-compose.yml`.
