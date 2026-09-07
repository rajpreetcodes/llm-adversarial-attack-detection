# ADR 0004: Offline-first fallbacks (SQLite, in-process cache, synthetic data)

## Status
Accepted.

## Context
The plan targets PostgreSQL, Redis, Hugging Face downloads, and paid LLM APIs.
CI, demos on a clean machine, and offline development cannot depend on any of
those being reachable, and API keys must never be required to boot.

## Decision
- `DATABASE_URL` defaults to SQLite; PostgreSQL remains the docker-compose
  default. SQLAlchemy makes the swap a connection string.
- `redis_url` unset means a bounded in-process cache (same interface).
- Channels that need external models (GPT-2, MiniLM, ollama, paid judges)
  lazy-load and degrade independently with a `degraded` flag; the pipeline
  never 500s because a model is missing, and fails CLOSED (escalate) if every
  cheap channel is down.
- The eval harness has a deterministic `--synthetic` mode (seeded) so the full
  ablation grid runs with zero downloads. Real-data mode uses the HF loaders.

## Consequences
- `pytest`, the API, the dashboard, and the ablation grid all run offline.
- Synthetic numbers are pipeline proof, not research results; the report must
  label them as such.
- Degraded behaviour is explicit and tested, not silent.

## Alternatives considered
- Require the full stack everywhere: rejected; CI and demos must be hermetic.
- Mock at test time only: rejected; the same fallbacks serve dev and demos.
