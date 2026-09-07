"""The disagreement gate. CORE NOVELTY of DGAD.

Prior systems fuse detector scores by averaging them. DGAD instead treats
*disagreement* between cheap channels as a routing signal: when calibrated
scores agree, the system decides immediately; when they disagree, only that
contested prompt escalates to expensive verification (behavioural probe and
LLM judge). See docs/adr/0001-disagreement-gating.md.

This module is pure logic with no model dependency, so it is tested
exhaustively. All thresholds come from Settings (config.py).
"""

import math
from collections.abc import Mapping, Sequence

import numpy as np

from dgad.config import Settings, get_settings
from dgad.schemas import Decision, GateDecision


def disagreement(scores: Mapping[str, float], metric: str = "abs_diff", *,
                 t_low: float = 0.3, t_high: float = 0.7) -> float:
    """Quantify how much calibrated channel scores disagree.

    Args:
        scores: calibrated score per channel name.
        metric: one of "abs_diff", "region_conflict", "entropy".
        t_low, t_high: decision band used by the region_conflict metric.

    Returns:
        A disagreement value. For abs_diff and region_conflict this is the
        max pairwise absolute difference (region_conflict zeroes it when no
        pair straddles the band); for entropy it is the binary entropy of the
        fused mean, which peaks when the ensemble is maximally unsure.
    """
    vals = list(scores.values())
    if len(vals) < 2:
        return 0.0
    max_diff = max(abs(a - b) for i, a in enumerate(vals) for b in vals[i + 1:])
    if metric == "abs_diff":
        return max_diff
    if metric == "region_conflict":
        straddles = any(s <= t_low for s in vals) and any(s >= t_high for s in vals)
        return max_diff if straddles else 0.0
    if metric == "entropy":
        p = min(max(float(np.mean(vals)), 1e-9), 1 - 1e-9)
        return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))
    raise ValueError(f"unknown disagreement metric: {metric}")


class DisagreementGate:
    """Three-way routing policy over calibrated channel scores.

    Policy (thresholds from Settings):
      * all scores <= t_low  -> PASS (channels agree benign)
      * all scores >= t_high -> BLOCK (channels agree attack)
      * disagreement >= t_d  -> ESCALATE (contested; the interesting case)
      * otherwise            -> fused mean decides (agreeing but in the
        uncertain middle band is rare once thresholds are tuned on validation)
    """

    def __init__(self, settings: Settings | None = None) -> None:
        s = settings or get_settings()
        self.t_low = s.gate_t_low
        self.t_high = s.gate_t_high
        self.t_d = s.gate_t_d
        self.metric = s.gate_disagreement_metric

    def decide(self, scores: Mapping[str, float]) -> GateDecision:
        """Route one prompt from its calibrated per-channel scores."""
        if not scores:
            raise ValueError("gate needs at least one channel score")
        vals = list(scores.values())
        d = disagreement(scores, self.metric, t_low=self.t_low, t_high=self.t_high)
        if all(v <= self.t_low for v in vals):
            decision = Decision.PASS
        elif all(v >= self.t_high for v in vals):
            decision = Decision.BLOCK
        elif d >= self.t_d:
            decision = Decision.ESCALATE
        else:
            fused = float(np.mean(vals))
            decision = Decision.BLOCK if fused >= (self.t_low + self.t_high) / 2 else Decision.PASS
        return GateDecision(
            decision=decision,
            scores=dict(scores),
            disagreement=d,
            rationale=None,
        )


def mean_fusion(scores: Mapping[str, float], threshold: float = 0.5) -> Decision:
    """Naive baseline: average the calibrated scores, threshold at 0.5."""
    if not scores:
        raise ValueError("fusion needs at least one channel score")
    return Decision.BLOCK if float(np.mean(list(scores.values()))) >= threshold else Decision.PASS


def max_fusion(scores: Mapping[str, float], threshold: float = 0.5) -> Decision:
    """Naive baseline: take the most suspicious channel, threshold at 0.5."""
    if not scores:
        raise ValueError("fusion needs at least one channel score")
    return Decision.BLOCK if max(scores.values()) >= threshold else Decision.PASS


def effective_score(scores: Mapping[str, float], gate: GateDecision,
                    escalation_score: float | None = None) -> float:
    """One scalar per prompt for ranking metrics, honouring the gate.

    PASS/BLOCK prompts use their fused mean; ESCALATEd prompts use the
    escalation tier's score when available (that is the whole point of
    spending money there) and fall back to the fused mean when it is not.
    """
    fused = float(np.mean(list(scores.values())))
    if gate.decision is Decision.ESCALATE and escalation_score is not None:
        return escalation_score
    return fused


def tune(
    channel_scores: Sequence[Mapping[str, float]],
    labels: Sequence[int],
    settings: Settings | None = None,
    n_trials: int = 100,
) -> dict:
    """Search gate thresholds on VALIDATION data only.

    Multi-objective in spirit: maximise ROC-AUC of the gated effective score
    subject to the escalation rate staying under the configured target,
    implemented as a hard penalty (final_plan.md Phase 5 step 3).

    Returns the best thresholds plus the per-trial (escalation rate, AUC)
    trade-off curve, which is a headline figure in the report.
    """
    import optuna
    from sklearn.metrics import roc_auc_score

    s = settings or get_settings()
    target = s.gate_escalation_rate_target
    y = np.asarray(labels)
    curve: list[dict] = []

    def objective(trial: "optuna.Trial") -> float:
        t_low = trial.suggest_float("t_low", 0.05, 0.45)
        t_high = trial.suggest_float("t_high", 0.55, 0.95)
        t_d = trial.suggest_float("t_d", 0.05, 0.6)
        gate = DisagreementGate(Settings(gate_t_low=t_low, gate_t_high=t_high, gate_t_d=t_d))
        decisions = [gate.decide(cs) for cs in channel_scores]
        esc_rate = float(np.mean([g.decision is Decision.ESCALATE for g in decisions]))
        eff = np.array(
            [effective_score(cs, g) for cs, g in zip(channel_scores, decisions, strict=True)]
        )
        auc = float(roc_auc_score(y, eff)) if len(set(y.tolist())) > 1 else 0.5
        curve.append({"escalation_rate": esc_rate, "roc_auc": auc})
        return auc - 10.0 * max(0.0, esc_rate - target)

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=s.random_seed),
    )
    study.optimize(objective, n_trials=n_trials)
    return {"best_params": study.best_params, "curve": curve}
