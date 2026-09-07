# DGAD: Disagreement-Gated Adaptive Detection

A security layer that sits in front of any LLM and inspects every prompt before it
reaches the model. Cheap detectors (statistical, semantic, representation offset)
score each prompt and are calibrated; when they agree, the system passes or blocks
immediately, and when they disagree, only that contested prompt is escalated to
expensive verification (a behavioural perturbation probe and an LLM-as-a-judge).
A self-adversarial calibration loop continuously searches for inputs that fool all
cheap detectors in the same direction (false agreement) and turns them into new
training data. The system is fully black-box and model-agnostic.

The authoritative implementation plan lives at
[../final_plan.md](../final_plan.md); repository conventions are in
[../AGENTS.md](../AGENTS.md).

## Quickstart

```bash
# Python 3.11 exactly; uv fetches it for you
uv venv --python 3.11

# CPU-only torch first, to avoid the multi-GB CUDA wheel
uv pip install torch --index-url https://download.pytorch.org/whl/cpu

# Project plus dev tooling
uv pip install -e ".[dev]"

# Quality gates
uv run ruff check .
uv run mypy src/
uv run pytest

# Real checkpoint build and training (set HF_TOKEN in the shell, never commit it)
uv run python -m dgad.eval.datasets --build
uv run python train_step1.py
uv run python evaluate_checkpoint.py

# Offline synthetic harness (deterministic CI evidence only)
uv run python -m dgad.eval.datasets --build --synthetic
uv run python -m dgad.eval.runner --all --synthetic
uv run python -m dgad.eval.report

# Run the API (versioned routes plus /detect, /proxy, /admin/stats, /admin/logs)
uv run uvicorn dgad.api.main:app --reload

# Dashboard (Node 20+): npm install && npm run dev, then http://localhost:5173
cd dashboard && npm install && npm run dev

# Or the full stack (api, postgres, redis)
docker compose up
```

## Layout

- `src/dgad/config.py`: every tunable threshold lives here (pydantic-settings).
- `src/dgad/schemas.py`: cross-module payload contracts.
- `src/dgad/channels/`: A statistical, B semantic, C behavioural, D judge, E offset.
- `src/dgad/calibration.py`: Platt/isotonic calibration (runs before the gate).
- `src/dgad/gate.py`: the disagreement gate (core novelty) + naive fusion baselines.
- `src/dgad/adversarial/`: mutation operators + self-adversarial loop (second novelty).
- `src/dgad/canary.py`: indirect-injection tripwire.
- `src/dgad/pipeline.py`: the full request flow, wired end to end.
- `src/dgad/eval/`: dataset builders, metrics, the 12-config ablation runner, report figures.
- `src/dgad/api/`, `src/dgad/storage/`: FastAPI routes + SQLAlchemy audit log (hashed prompts).
- `dashboard/`: React + Vite + Tailwind + MUI + Recharts (Utilitarian style, ADR 0005).
- `results/`: generated checkpoint metrics, score tables, and figures with provenance.
- `tests/{unit,integration,adversarial}/`: three test tiers.
- `docs/adr/`: architecture decision records; `docs/runbook.md`; `docs/viva_prep.md`.
