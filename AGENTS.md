# AGENTS.md

Guidance for AI coding agents working in this repository. Read this before making any change.

## Project Overview

This is a university capstone project (SVKM's NMIMS, Mukesh Patel School of Technology Management & Engineering, Mumbai Campus, IT Department, Semester 7).

**Project title:** Adversarial Attack Detection for Large Language Models (LLMs)
**System name:** DGAD (Disagreement-Gated Adaptive Detection)
**Team:** Rajpreet Singh Khurana (K033), Dhruv Rathod (K055), Sumit Pandey (K044)
**Mentor:** Dr. Ruchi Sharma

DGAD is a planned security layer that sits in front of any LLM and inspects every prompt before it reaches the model. Its core research idea: instead of averaging the scores of several detectors (the standard approach), it treats **disagreement between cheap detectors as a routing signal**. When the cheap statistical and semantic detectors agree, the system decides immediately; when they disagree, only that contested prompt is escalated to expensive verification (a black-box behavioural probe and an LLM-as-a-judge). A self-adversarial calibration loop continuously searches for inputs that fool all cheap detectors in the same direction (false agreement) and turns them into new training data. The system is fully black-box and model-agnostic.

The target attack categories (from the synopsis, Section 6): optimisation-based jailbreaks (GCG-style suffixes and fluent variants), prompt injection (direct and indirect), and role-play/persona jailbreaks. Explicitly out of scope: multi-turn attacks, multimodal injections, non-English prompts, and training-time attacks (poisoning, backdoors).

## Current Repository State (important)

**The codebase now exists under `main/`** (built 2026-08-13 per `final_plan.md`): full `src/dgad/` package (config, schemas, normalise, channels A-E, calibration, disagreement gate, canary, adversarial loop, pipeline, eval harness, FastAPI API + SQLAlchemy storage), three test tiers (94 tests), React dashboard in `main/dashboard/`, Docker/CI/alembic scaffolding, ADRs 0001-0005, runbook, and viva prep docs. Offline-first defaults: SQLite default DB (Postgres via docker compose), in-process cache when Redis is unset, deterministic `--synthetic` eval mode requiring zero downloads, graceful per-channel degradation when models/services are missing. The quality gates below all run and pass inside `main/` (use `main/.venv/Scripts/python.exe` or `uv run`).

The planning documents remain at the repo root:

- `final_plan.md`: the authoritative, detailed implementation plan ("DGAD: Complete Implementation Plan, Start to Finish"). This is the single source of truth for architecture, phases, library choices, team ownership, and the CAMS DevOps procedure. Read it before designing anything.
- `Final_Synopsis.md` / `Final_Synopsis.pdf`: the official project synopsis (problem statement, literature survey, objectives, evaluation metrics, hardware/software requirements, deliverables). The PDF is a scanned document; the .md is an OCR extraction of it.
- `Novel_Method_Proposal.md`: an earlier draft ("PRISM") responding to the mentor's novelty objection; superseded by the DGAD framing in `final_plan.md`.
- `DGAD Implementation Plan (standalone).html`: a self-contained HTML rendering of the same plan.
- `Capstone_Plan.pdf`, `PLANNNN.pdf`, `Group10_synopsis.pdf`, `Automated_Adversarial_Attack_Detection_LLM_Synopsis1.pdf`, `Adversarial_Attack_Detection_LLM_Synopsis_v2.docx`, `Final_synopsis.pptx`, `Synopsis_template.pptx`: earlier drafts and presentation material.
- `.git/`: version history.

## Planned Architecture

One repository, one Python package (explicitly not microservices). Target layout from `final_plan.md` section 4:

```
dgad/
├── pyproject.toml              <- dependencies and tool config (uv, ruff, mypy)
├── .pre-commit-config.yaml
├── .env.example                <- secret NAMES only, never values
├── docker-compose.yml          <- services: api, postgres, redis
├── Dockerfile
├── .github/workflows/          <- ci.yml, eval.yml (nightly benchmark), security.yml
├── data/{raw,interim,processed}/  <- all gitignored; data/README.md documents sources and licenses
├── src/dgad/
│   ├── config.py               <- pydantic-settings; ALL thresholds live here
│   ├── schemas.py              <- pydantic models for every payload
│   ├── normalise.py            <- unicode + de-obfuscation preprocessing
│   ├── channels/
│   │   ├── base.py             <- abstract Channel: score(text) -> ChannelResult
│   │   ├── statistical.py      <- Channel A: windowed perplexity + token anomaly
│   │   ├── semantic.py         <- Channel B: embedding classifier
│   │   ├── behavioural.py      <- Channel C: perturbation-consistency probe (escalation only)
│   │   ├── judge.py            <- Channel D: LLM-as-a-judge (escalation only)
│   │   └── offset.py           <- Channel E: black-box representation offset
│   ├── calibration.py          <- Platt / isotonic calibration, reliability curves
│   ├── gate.py                 <- THE DISAGREEMENT GATE (core novelty)
│   ├── canary.py               <- indirect-injection tripwire
│   ├── adversarial/{mutators.py,loop.py}  <- self-adversarial calibration loop
│   ├── api/                    <- FastAPI app: routes_detect, routes_proxy, routes_admin
│   ├── storage/                <- SQLAlchemy + Alembic (PostgreSQL audit log)
│   └── eval/                   <- dataset loaders, metrics, ablation runner, report generator
├── dashboard/                  <- React + Vite + TypeScript + Tailwind + MUI + Recharts
├── notebooks/                  <- exploration only, NEVER imported by src
├── tests/{unit,integration,adversarial}/
└── docs/adr/                   <- architecture decision records, runbook, viva prep
```

Request flow: normalise prompt -> Channels A, B, E (cheap) -> calibration layer -> disagreement gate. Agreement means immediate PASS or BLOCK; disagreement escalates to Channels C and D for a final decision with rationale. Calibration must run **before** the gate, because raw scores from different channels are not comparable. All decisions are logged to PostgreSQL and surfaced on the dashboard.

The central interface contract (Phase 0, step 6): every channel implements `score(text: str) -> ChannelResult` where `ChannelResult` carries `raw_score: float`, `calibrated_score: float | None`, `latency_ms: float`, `metadata: dict`. Do not break this contract; the ablation study depends on channels being swappable without rewriting anything.

## Technology Stack (planned)

- **Language/runtime:** Python 3.11 exactly (not 3.12/3.13; ML wheels lag). Node 20 LTS for the dashboard only.
- **Dependency management:** `uv` (produces a lockfile). FastAPI + Uvicorn for the API and LLM proxy.
- **ML:** PyTorch (CPU build locally, CUDA build only on the cloud GPU box), Hugging Face Transformers, sentence-transformers (`all-MiniLM-L6-v2` default embedder), scikit-learn (classifier heads + calibration), GPT-2 as the perplexity reference model.
- **Storage/cache:** PostgreSQL (SQLAlchemy + Alembic + psycopg), Redis for score caching.
- **LLM access:** `anthropic`, `openai`, `ollama` (local models strongly recommended for the behavioural probe), optional `litellm`.
- **Attack/red-team tooling:** `nlpaug`, `textattack`, `garak`, `promptfoo`.
- **Observability:** structlog, prometheus-client, OpenTelemetry, MLflow or W&B (pick one) for experiment tracking.
- **DevOps:** Docker + Docker Compose (WSL2 backend on Windows), GitHub Actions.
- **Dashboard:** React, Vite, TypeScript, Tailwind CSS, Material UI, Recharts, TanStack Query, axios, zod.

Note: the synopsis mentions a Node.js/Express gateway, but `final_plan.md` section 12 records the team's decision to propose **FastAPI-only** (one backend) pending mentor sign-off. Do not scaffold an Express layer unless that decision is reversed.

Hardware note (from the plan): a 6 GB VRAM GPU covers everything except Llama-Guard-3-8B and fresh GCG attack reproduction; those two need one cloud GPU session.

## Build and Test Commands (planned, per Phase 0)

```bash
# One-time setup
uv venv --python 3.11
uv pip install -e ".[dev]"
pre-commit install

# Reproduce the benchmark dataset from a fixed seed
python -m dgad.eval.datasets --build

# Run the full evaluation / ablation grid
python -m dgad.eval.runner --all

# Quality gates (also run by pre-commit and CI)
ruff check . && ruff format .
mypy src/
pytest                      # unit + integration
pytest tests/adversarial/   # attack regression suite
bandit -r src/ && pip-audit

# Run the stack
docker compose up           # api, postgres, redis; GET /health must respond
```

None of these work today; they become valid once Phase 0 scaffolding exists.

## Development Conventions

- **Branching:** `main` is always deployable. Work on `feat/<name>-<thing>`, squash-merge via PR. Tag `v0.1`, `v0.2`, ... at each phase boundary so a working older version is always demoable.
- **Commits:** conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- **Reviews:** nobody merges their own PR; one approving review from another team member is required, no exceptions. Branch protection on `main` enforces CI green + one approval.
- **Decision records:** every non-obvious choice gets a one-page ADR in `docs/adr/` (first one: `0001-disagreement-gating.md`, why gating over score averaging). Blameless post-mortems also live there.
- **Config:** all thresholds and tunables live in `src/dgad/config.py` (pydantic-settings). No magic numbers scattered in channel code.
- **Docstrings:** required on public functions, especially in `gate.py` and `calibration.py`.
- **Notebooks** are for exploration only and must never be imported from `src/`.
- **Report tables and figures are generated files** (from the eval runner), never hand-typed. Dataset splits are built from a fixed seed; nobody hand-edits a CSV.
- **Rule of three:** if you do something manually for the third time, automate it that day.
- **Language:** all documentation and comments are in English (British spelling appears in the plan, e.g. "normalise").

## Testing Strategy

- `pytest` with `pytest-cov` and `pytest-asyncio`; `hypothesis` for property-based tests (e.g. normaliser idempotence: normalising twice equals normalising once).
- Three test tiers: `tests/unit/`, `tests/integration/`, and `tests/adversarial/` (attack regression suite: CI fails if a previously blocked attack starts passing).
- Data-layer tests must prove zero leakage between train/val/test/holdout splits. Splits are grouped by attack family and source, never random, because near-duplicate jailbreak variants would otherwise leak across splits.
- A `holdout` split is reserved and untouched until the final evaluation (Phase 13). Never tune anything on it.
- `locust` for load/throughput testing; a nightly GitHub Action runs the full benchmark on the validation split to catch silent regressions.
- Evaluation metrics that matter: ROC-AUC, PR-AUC, precision/recall/F1, FPR (including over-defense FPR on the NotInject benign set, tracked separately), Expected Calibration Error, escalation rate, cost per 1,000 prompts vs judge-on-everything, and p50/p95/p99 latency per channel.

## Deployment and CI/CD

Planned pipeline (CAMS framework, `final_plan.md` section 8): pre-commit hooks (ruff, mypy, detect-secrets) -> GitHub Actions on push (lint, type check, unit + integration tests, bandit + pip-audit, adversarial regression suite) -> peer review -> squash merge to `main` -> Docker image build -> staging deploy + smoke test -> nightly full benchmark posting metrics to MLflow + Prometheus. Database schema changes go through Alembic only; nobody runs manual SQL against a shared database.

## Security Considerations

- **Secrets:** `.env` is gitignored; `.env.example` lists secret names only (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DATABASE_URL`). `detect-secrets` runs in pre-commit and is non-negotiable. Verify `.env` is ignored before the first commit.
- **Datasets are never committed.** `data/raw`, `data/interim`, `data/processed` are gitignored; `data/README.md` documents every source with URL, license, row counts, and download date.
- **Scanning:** `bandit` (insecure Python patterns) and `pip-audit` (dependency CVEs) run in CI on every push and weekly.
- This project is itself a security tool, so it must expect adversarial input everywhere: the detector is an attack surface (evasion attacks against guardrails are an explicit evaluation category), and the red-team phase (garak, promptfoo) attacks our own detector, including the LLM judge.
- When reporting dataset sizes or results, never quote raw row counts; report the funnel (total -> after dedup -> after quality filter -> final). Never invent numeric targets or results retroactively; targets are agreed with the mentor in advance and written into the repo before evaluation.

## Team Ownership (from the plan)

| Owner | Primary slice |
| :--- | :--- |
| Rajpreet Singh Khurana (K033) | Channels C, D, E; self-adversarial calibration loop; red-teaming |
| Dhruv Rathod (K055) | Data layer; Channels A and B; calibration; disagreement gate; evaluation harness |
| Sumit Pandey (K044) | FastAPI proxy, database/audit logging, dashboard, Docker, CI/CD |

Each owner also writes the tests and docs for their slice; every module has a named reviewer from another member. The critical path is: data layer -> Channels A/B -> calibration -> disagreement gate -> final ablation. Calibration and the gate cannot slip; everything downstream depends on them.
