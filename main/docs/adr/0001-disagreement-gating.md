# ADR 0001: Disagreement Gating Over Score Averaging

- Status: accepted
- Date: 2026-08-13
- Deciders: Rajpreet Singh Khurana, Dhruv Rathod, Sumit Pandey

## Context

DGAD runs several detectors on every prompt and must combine their outputs into
one decision. The standard approach in existing systems is score fusion: average
(or vote) the detector scores and threshold the result. If detector A says 0.2 and
detector B says 0.9, fusion yields 0.55 and the system shrugs.

Our cheap channels have deliberately complementary blind spots. Channel A
(statistical, windowed perplexity) catches gibberish optimisation-based suffixes
but is blind to fluent, well-written jailbreaks. Channel B (semantic embedding
classifier) catches role-play and "ignore previous instructions" attacks but is
blind to novel phrasings and tends to over-defend on innocent trigger words.
Expensive verification (Channel C behavioural probe, Channel D LLM-as-a-judge)
is accurate but too slow and costly to run on every prompt.

## Decision

We treat disagreement between the cheap channels as the primary routing signal,
not as a number to average away. After calibration (so scores are comparable),
the gate applies a three-way policy:

- All channels below `t_low`: PASS immediately.
- All channels above `t_high`: BLOCK immediately.
- Channels disagree by more than `t_d`: ESCALATE only that prompt to the
  expensive tier (Channels C and D) for a final decision with a rationale.

Thresholds are tuned on the validation split only, maximising ROC-AUC subject
to an escalation-rate constraint (target: no more than 15 percent of traffic).

## Consequences

Positive:

- Cost: expensive detectors run only on the contested subset, so average
  latency and cost per 1,000 prompts are far below judge-on-everything. This
  is measurable, which makes the novelty evaluable rather than architectural.
- Information: disagreement is precisely the case where one channel's blind
  spot is exposed. Pulling those prompts aside for verification uses the only
  interesting information fusion would discard.
- The escalation rate becomes a headline, controllable trade-off knob.

Negative / risks:

- Two-stage routing adds gate complexity and three thresholds to tune.
- An adaptive attacker who makes all cheap channels agree wrongly (false
  agreement) bypasses escalation entirely. This is mitigated by the
  self-adversarial calibration loop, which specifically searches for
  false-agreement inputs and turns them into new training data.

## Alternatives considered

- Naive score averaging / voting: discarded, it throws away the disagreement
  signal and still pays for a decision made in the dark.
- Judge on everything: discarded, latency and API cost are unacceptable at
  production traffic volumes.
- Single best detector: kept as an evaluation baseline, not as the design.
