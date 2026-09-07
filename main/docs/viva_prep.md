# Viva Preparation: the 22 questions, answered

Every member answers ALL of these, not just their own slice. Sources:
final_plan.md sections 1, 2, 7; the code as built.

## Novelty

1. **What is new, one sentence?** We use disagreement between cheap detectors
   as a routing signal that sends only contested prompts to expensive
   verification, instead of averaging scores away.

2. **Versus averaging?** Averaging 0.2 and 0.9 yields 0.55 and discards the
   only interesting information: that the channels conflict. We route on that
   conflict. It is also measurably cheaper: the judge sees ~the contested
   slice, not 100% of traffic.

3. **DataSentinel difference?** It fine-tunes one canary model with minimax
   game theory. Our loop optimises against cross-channel FALSE AGREEMENT in a
   multi-detector black-box system: different objective, different level
   (system, not model).

4. **Is the behavioural probe the failed semantic-entropy method?** The
   Consistency Confound showed consistency fails ALONE (85 to 98% false
   negatives). We never use it alone: it is one tie-breaker on the small
   contested subset. We cite the negative result ourselves.

5. **ROD already measures intent offset?** ROD reads hidden states
   (white-box). Ours is a black-box approximation via intent extraction plus
   embedding distance. We claim only the adaptation and cite ROD as
   inspiration.

## Method

6. **Why calibration before the gate?** Channel A outputs perplexity-scale
   numbers, Channel B probabilities. "Disagreement" is meaningless until both
   are honest probabilities on the same scale. Calibration runs on the
   validation split only, then the gate.

7. **Threshold choice and overfitting?** t_low, t_high, t_d tuned with optuna
   on the validation split, constrained on escalation rate (<= 15%). The
   holdout split is locked until the final evaluation, so thresholds never
   see it. Operating thresholds use Youden's J on validation.

8. **Both cheap channels wrong in the same direction?** That is the false-
   agreement hole, and it is exactly what the self-adversarial loop hunts:
   it mutates known attacks until all cheap channels agree benign, verifies
   intent with the judge, and turns survivors into hard-negative training data.

9. **Why this escalation rate?** It is a chosen operating point on the
   measured escalation-rate vs AUC curve (results/figures/escalation_vs_auc.png).
   Halving it moves along that curve: cheaper, less accurate on contested
   inputs. The dashboard playground demonstrates this live.

10. **Proxy model validity for the probe?** We measure prompt brittleness,
    not the protected model's alignment. An optimised suffix tuned against one
    model family loses its effect under perturbation regardless of which small
    model observes the compliance swing. We report this assumption openly.

## Evaluation

11. **No leakage?** Splits are grouped by attack family and source, never
    random; variants of one prompt stay on one side. tests/unit/test_datasets.py
    proves zero normalised-text overlap between splits.

12. **Confidence intervals?** Bootstrap with 1000 resamples on every headline
    AUC (roc_auc_ci_lo/hi in ablation.csv). Overlapping intervals are reported
    as not significant, not spun.

13. **FPR on trigger-word prompts?** Tracked separately as notinject_fpr in
    every ablation row (NotInject-style benign prompts stuffed with "ignore",
    "password", "bomb").

14. **Worst attack family?** Answer from the per-family figure
    (results/figures/per_family_auc.png). On synthetic data: role-play is the
    hardest for the statistical channel; that blind spot is the design's
    founding observation.

15. **What did NOT contribute?** Have the ablation open. If Channel C adds
    nothing (expected per the Consistency Confound), say so: a documented null
    result for one channel does not sink the system.

## Security

16. **Judge as attack surface?** The judged prompt is wrapped as
    data-never-instructions, and the judge's system prompt carries a per-call
    random canary. A judge reply that drops the canary is flagged hijacked
    (test: test_canary_hijack_detected). Fail-closed on unparseable output.

17. **What evaded us in red-teaming?** See tests/adversarial/: ROT13 of
    fluent text currently evades Channel A alone (frozen regression test
    documents the gap); homoglyphs, zero-width, base64, and spacing tricks are
    caught. Zero findings would be suspicious; we report the real ceiling.

18. **Judge API down?** Circuit breaker opens after 3 consecutive failures;
    the pipeline degrades to the gate's decision with a degraded flag instead
    of failing the request.

19. **Prompt storage?** We store SHA-256 hashes of normalised prompts by
    default. Raw storage is an explicit opt-in. Integration test proves raw
    text never reaches the database by default.

## Engineering

20. **One request, end to end?** normalise -> Channels A, B, E (cheap) ->
    calibration -> disagreement gate. Agree: instant PASS/BLOCK. Disagree:
    escalate to behavioural probe + LLM judge, final decision with rationale.
    Every step is logged to the audit DB and visible on the dashboard.

21. **Deploy in front of an existing app?** One-line change: point the OpenAI
    client base URL at our /v1/chat/completions. Policy modes block /
    flag_and_pass / observe_only mirror real security rollouts: observe first,
    enforce later.

22. **How do you know a change did not break detection?** The adversarial
    regression suite fails CI if a previously blocked evasion starts passing,
    and the nightly eval workflow re-runs the benchmark on the validation
    split to catch silent quality regressions.
