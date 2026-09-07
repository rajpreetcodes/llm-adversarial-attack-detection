# DGAD checkpoint verification

Verified on 7 September 2026 at repository commit `d43f18fc448f5f5512f2e64ead3dec8956b910c3` plus the current working changes.

## Reproduced evidence

| Check | Result |
|---|---|
| Authenticated real-data build | 93,211 raw → 53,428 deduplicated examples |
| Splits | train 32,077; validation 8,007; test 8,007; locked holdout 5,337 |
| Leakage check | zero normalized prompt duplicates across splits |
| NotInject | 255 usable benign controls across splits; 38 in test |
| Training | feature-only Channel A and MiniLM Channel B fitted on 3,000 seeded training rows each |
| Calibration | validation-only Platt calibrators saved for A, B and E |
| Gate | `t_low=0.1998`, `t_high=0.9303`, `t_d=0.4526`; tuned on validation only |
| Test evaluation | Channel B ROC-AUC 0.8604, 95% bootstrap CI 0.8529–0.8685, n=8,007 |
| Over-defence | Channel B NotInject FPR 39.47% at threshold 0.5; this is a known checkpoint weakness |
| Python tests | 100 passed, one third-party deprecation warning |
| Type check | mypy passed: 31 source files |
| Dashboard | production build passed; live injection example returned BLOCK with raw/calibrated traces |
| Local escalation tier | Ollama `qwen2.5:1.5b-instruct` installed; judge and behavioural probe responded |

The live benign request escalated and passed with all channels healthy. The cold/warm mixed end-to-end latency was 73.9 seconds because the behavioural path makes six serial local-model calls. The direct injection example was blocked on the cheap path in 2.7–3.4 seconds. These are demo observations on this laptop, not latency benchmarks.

## Claims that remain out of scope for this checkpoint

- Channel A is feature-only. GPT-2 windowed-perplexity training remains pending.
- The test evaluator reports A/B and naive fusion. It deliberately does not label unresolved gate cases as a measured full-DGAD score.
- A complete real C/D benchmark, cost accounting, latency percentiles, held-out family experiments and the self-adversarial hardening loop remain final-phase work.
- The older committed ablation files have mixed row counts and cannot support research claims. `DGAD_Score_Provenance.json` records the mismatch.
- The current NotInject false-positive rate is high and must be reduced through threshold work and targeted hard-negative training.
