# DGAD Runbook

How to set up, run, evaluate, and fix DGAD on a clean machine. Follow this
literally; it is tested as the demo procedure.

## Setup (10 minutes)

```bash
cd main
uv venv --python 3.11
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install -e ".[dev]"
```

Node 20+ for the dashboard only. Docker Desktop for the containerised run.

## Run the API

```bash
cd main
.venv/Scripts/python.exe -m uvicorn dgad.api.main:app --port 8000
```

- `GET /health` must return `{"status": "ok"}`.
- `POST /v1/detect` with `{"prompt": "..."}` returns decision, per-channel
  scores, disagreement, latency.
- `POST /v1/chat/completions` is the OpenAI-compatible proxy; point any
  OpenAI client at `http://localhost:8000/v1`.
- Without trained channel heads the API still boots: affected channels
  report `degraded: true` instead of crashing.

## Run the dashboard

```bash
cd main/dashboard
npm install
npm run dev        # http://localhost:5173, proxies to :8000
```

If the API is down the dashboard shows a retryable error. It never substitutes
mock telemetry for measured detector output.

## Build the dataset and run the evaluation

```bash
# Authenticated real-data build. Set HF_TOKEN only in the current shell.
HF_TOKEN=... python -m dgad.eval.datasets --build

# Fit Channels A/B, validation-only Platt calibrators, and the gate.
python train_step1.py

# Honest checkpoint evaluation of trained cheap channels on the test split.
python evaluate_checkpoint.py

# Offline synthetic harness for CI and pipeline checks; never cite as research evidence.
python -m dgad.eval.runner --all --synthetic

# regenerate every report figure from the raw CSVs
python -m dgad.eval.report
```

Real checkpoint outputs land in `results/checkpoint_metrics.csv`,
`results/checkpoint_scores.csv`, `results/train_meta.json`, and
`results/figures/calibration_*.png`. The broader synthetic harness writes its
own ablation files; keep their provenance label when presenting them.

**Holdout discipline:** the holdout split is never touched until the final
evaluation. Then, and only then: `--holdout`.

## Docker

```bash
docker compose up   # api + postgres + redis; GET /health must respond
```

## Quality gates

```bash
ruff check . && ruff format .
mypy src/
pytest                      # unit + integration
pytest tests/adversarial/   # evasion regression suite
```

## When things break

| Symptom | Likely cause | Fix |
| :--- | :--- | :--- |
| `/v1/detect` returns all-degraded | no trained heads, no ollama | run the eval runner once (trains + saves to `models/`) |
| judge calls fail | no API key / ollama down | circuit breaker degrades to neutral after 3 failures; check `judge_provider` in config |
| DB errors on startup | `DATABASE_URL` unreachable | default is local SQLite `dgad.db`; check env |
| dashboard error banner | API down | start the API, then use Retry |
| `pytest` slow on first run | torch import | normal; subsequent runs are fast |

## Known limitations (say them before the examiner does)

- Synthetic-mode numbers are pipeline proof, not research results; the real
  benchmark runs on the HF datasets.
- The behavioural probe and judge need a local Ollama model
  (`ollama pull qwen2.5:1.5b-instruct`); without it they degrade gracefully.
- The checkpoint training script uses feature-only Channel A. GPT-2 windowed
  perplexity training and a full C/D real benchmark remain final-phase work.
- ROT13-style encodings of fluent text currently evade Channel A (frozen as
  a regression test in tests/adversarial/).
