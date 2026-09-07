"""Evaluation metrics (final_plan.md Phase 13).

Every headline number carries a bootstrap confidence interval: a 0.3 percent
AUC gap with overlapping intervals is not a result.
"""

import numpy as np
import pandas as pd
from sklearn import metrics as skm


def detection_metrics(y_true: np.ndarray, y_score: np.ndarray,
                      threshold: float = 0.5) -> dict:
    """The full detection-quality bundle at one operating threshold."""
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    y_pred = (y_score >= threshold).astype(int)
    out = {
        "roc_auc": float(skm.roc_auc_score(y_true, y_score)),
        "pr_auc": float(skm.average_precision_score(y_true, y_score)),
        "accuracy": float(skm.accuracy_score(y_true, y_pred)),
        "precision": float(skm.precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(skm.recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(skm.f1_score(y_true, y_pred, zero_division=0)),
    }
    tn, fp, fn, tp = skm.confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    out["fpr"] = float(fp / (fp + tn)) if (fp + tn) else 0.0
    out["fnr"] = float(fn / (fn + tp)) if (fn + tp) else 0.0
    return out


def bootstrap_auc_ci(y_true: np.ndarray, y_score: np.ndarray,
                     n_resamples: int = 1000, seed: int = 42,
                     alpha: float = 0.05) -> tuple[float, float]:
    """Bootstrap CI on ROC-AUC (>= 1000 resamples per the plan)."""
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    n = len(y_true)
    aucs = []
    for _ in range(n_resamples):
        idx = rng.integers(0, n, n)
        if len(set(y_true[idx].tolist())) < 2:
            continue
        aucs.append(skm.roc_auc_score(y_true[idx], y_score[idx]))
    lo, hi = np.percentile(aucs, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def per_family(df: pd.DataFrame, score_col: str = "score",
               label_col: str = "label", family_col: str = "attack_family") -> pd.DataFrame:
    """Per-attack-family metrics; aggregates hide the complementarity story."""
    rows = []
    for family, sub in df.groupby(family_col):
        if sub[label_col].nunique() < 2:
            rows.append({family_col: family, "roc_auc": float("nan"), "n": len(sub)})
            continue
        rows.append({
            family_col: family,
            "n": len(sub),
            **detection_metrics(sub[label_col].to_numpy(), sub[score_col].to_numpy()),
        })
    return pd.DataFrame(rows)


def latency_percentiles(latencies_ms: np.ndarray) -> dict:
    """p50 / p95 / p99 latency, per channel or end to end."""
    arr = np.asarray(latencies_ms, dtype=float)
    return {f"p{p}": float(np.percentile(arr, p)) for p in (50, 95, 99)}


def cost_per_1000(n_prompts: int, n_judge_calls: int, judge_call_cost: float,
                  n_probe_calls: int = 0, probe_call_cost: float = 0.0) -> float:
    """Estimated currency cost per 1,000 prompts for one configuration."""
    if n_prompts == 0:
        return 0.0
    total = n_judge_calls * judge_call_cost + n_probe_calls * probe_call_cost
    return total / n_prompts * 1000
