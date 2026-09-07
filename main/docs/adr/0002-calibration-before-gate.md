# ADR 0002: Calibration runs before the gate

## Status
Accepted.

## Context
Channel A emits perplexity-scale numbers (tens to hundreds), Channel B emits
probabilities, Channel E emits cosine distances. The disagreement gate compares
channel scores; comparing raw values across different scales would measure the
scales, not the disagreement.

## Decision
Every channel's raw score passes through a per-channel calibrator (Platt or
isotonic, chosen on validation, persisted with joblib) fitted on the
validation split ONLY, before the gate sees the score. The gate consumes
calibrated probabilities exclusively.

## Consequences
- Disagreement values are real information, not scale artefacts.
- Calibration quality is itself measured (ECE before/after, reliability
  diagrams) and reported.
- Calibrators must be re-fit whenever a channel is retrained (the adversarial
  loop does this in its hardening step).

## Alternatives considered
- Normalising raw scores (z-score): discarded; ranking is preserved but
  probabilities stay meaningless, and ECE cannot be reported.
- Feeding raw scores to the gate: discarded; it is the bug this ADR exists to
  prevent.
