"""Ablation runner (final_plan.md Phase 13).

Runs the full 12-configuration ablation grid through one identical harness
and writes every table as a generated CSV (report tables are generated
files, never hand-typed). In --synthetic mode the whole grid runs offline:
cheap channels use the hashing embedder and feature-only statistics, and the
judge is a scripted noisy oracle standing in for a paid API (its accuracy,
latency, and cost are simulation parameters, clearly labelled as such; real
runs swap in JudgeChannel without touching the harness).

Usage:
    python -m dgad.eval.runner --all --synthetic
    python -m dgad.eval.runner --all --synthetic --holdout   # final eval only
"""

import argparse
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dgad.calibration import Calibrator
from dgad.channels.behavioural import BehaviouralChannel
from dgad.channels.semantic import SemanticChannel, hashing_embedder
from dgad.channels.statistical import StatisticalChannel
from dgad.config import Settings, get_settings
from dgad.eval import metrics as ev
from dgad.gate import DisagreementGate, effective_score, max_fusion, mean_fusion, tune
from dgad.normalise import normalise
from dgad.schemas import Decision

# The 12-config ablation grid (final_plan.md Phase 13 step 2).
# fusion: gate | mean | max | single; escalation: none | judge | judge_probe
ABLATION_GRID: list[dict] = [
    {"id": 1, "name": "channel_a_only", "channels": ["statistical"],
     "fusion": "single", "escalation": "none"},
    {"id": 2, "name": "channel_b_only", "channels": ["semantic"],
     "fusion": "single", "escalation": "none"},
    {"id": 3, "name": "deberta_guard_only", "channels": ["guard:deberta"],
     "fusion": "single", "escalation": "none"},
    {"id": 4, "name": "prompt_guard_only", "channels": ["guard:promptguard"],
     "fusion": "single", "escalation": "none"},
    {"id": 5, "name": "judge_on_everything", "channels": ["judge"],
     "fusion": "single", "escalation": "none"},
    {"id": 6, "name": "naive_mean_fusion", "channels": ["statistical", "semantic"],
     "fusion": "mean", "escalation": "none"},
    {"id": 7, "name": "naive_max_fusion", "channels": ["statistical", "semantic"],
     "fusion": "max", "escalation": "none"},
    {"id": 8, "name": "dgad_no_escalation", "channels": ["statistical", "semantic"],
     "fusion": "gate", "escalation": "none"},
    {"id": 9, "name": "dgad_escalate_judge", "channels": ["statistical", "semantic"],
     "fusion": "gate", "escalation": "judge"},
    {"id": 10, "name": "dgad_offset_judge",
     "channels": ["statistical", "semantic", "offset"],
     "fusion": "gate", "escalation": "judge"},
    {"id": 11, "name": "dgad_full",
     "channels": ["statistical", "semantic", "offset"],
     "fusion": "gate", "escalation": "judge_probe"},
    {"id": 12, "name": "dgad_full_hardened",
     "channels": ["statistical", "semantic", "offset"],
     "fusion": "gate", "escalation": "judge_probe", "hardened": True},
]

# Synthetic judge simulation parameters (labelled honestly in the report):
# a strong judge is right most of the time, slow, and costs money.
SYNTH_JUDGE_ACCURACY = 0.92
SYNTH_JUDGE_LATENCY_MS = 800.0
SYNTH_PROBE_LATENCY_MS = 300.0


def make_synthetic_judge(seed: int) -> Callable[[str, int], float]:
    """Scripted judge for offline runs: returns calibrated-looking score.

    Correct with probability SYNTH_JUDGE_ACCURACY; needs the true label, so
    it exists ONLY inside the synthetic harness, never in production code.
    """
    rng = np.random.default_rng(seed)

    def judge(text: str, label: int) -> float:
        correct = rng.random() < SYNTH_JUDGE_ACCURACY
        if correct:
            return float(rng.uniform(0.75, 0.98) if label == 1 else rng.uniform(0.02, 0.25))
        return float(rng.uniform(0.6, 0.9) if label == 0 else rng.uniform(0.1, 0.4))

    return judge


def build_cheap_channels(settings: Settings, train_df: pd.DataFrame,
                         hardened: bool = False) -> dict:
    """Train/fit the cheap channels on the TRAIN split (synthetic mode).

    hardened=True simulates Phase 10: Channel B retrained with the hard
    negatives the adversarial loop found (here: obfuscation and role-play
    variants appended as extra attack data).
    """
    texts = train_df["text"].tolist()
    labels = train_df["label"].tolist()
    if hardened:
        extra = train_df[train_df["attack_family"].isin(["obfuscation", "jailbreak_roleplay"])]
        texts = texts + extra["text"].tolist()
        labels = labels + [1] * len(extra)
    # train with GPT-2 so the persisted combiner matches API serving mode;
    # probe availability first (feature extraction itself never raises)
    from dgad.channels.statistical import _load_gpt2

    use_model = True
    try:
        _load_gpt2(settings.perplexity_model)
    except Exception:
        use_model = False
    ch_a = StatisticalChannel(settings, use_model=use_model)
    ch_a.fit(texts, labels)
    ch_b = SemanticChannel(settings, embedder=hashing_embedder())
    ch_b.fit(texts, labels)
    from dgad.channels.offset import OffsetChannel, heuristic_intent_extractor

    ch_e = OffsetChannel(settings, extractor=heuristic_intent_extractor,
                         embedder=hashing_embedder())
    return {"statistical": ch_a, "semantic": ch_b, "offset": ch_e}


def fit_calibrators(channels: dict, val_df: pd.DataFrame,
                    settings: Settings) -> dict[str, Calibrator]:
    """Fit one calibrator per cheap channel on the VALIDATION split only."""
    calibrators = {}
    for name, ch in channels.items():
        if name == "offset":
            raw = np.array([ch.score(t).raw_score for t in val_df["text"]])
        else:
            raw = np.array([ch.score(t).raw_score for t in val_df["text"]])
        calibrators[name] = Calibrator(name, settings=settings).fit(
            raw, val_df["label"].to_numpy()
        )
    return calibrators


def run_config(cfg: dict, df: pd.DataFrame, channels: dict,
               calibrators: dict[str, Calibrator], gate: DisagreementGate,
               judge_fn: Callable[[str, int], float] | None,
               settings: Settings) -> pd.DataFrame:
    """Run one ablation configuration over a split. Returns per-row scores."""
    if any(c.startswith("guard:") for c in cfg["channels"]):
        raise RuntimeError("guard-model configs require downloaded models")
    rows = []
    probe = BehaviouralChannel(settings, probe=lambda p: "ok")
    for rec in df.itertuples():
        text = normalise(rec.text)
        t0 = time.perf_counter()
        channel_scores: dict[str, float] = {}
        latency = 0.0
        n_judge = 0
        n_probe = 0
        if cfg["channels"] == ["judge"]:
            assert judge_fn is not None
            score = judge_fn(text, rec.label)
            latency += SYNTH_JUDGE_LATENCY_MS
            n_judge = 1
            decision = Decision.BLOCK if score >= 0.5 else Decision.PASS
            rows.append(_row(rec, score, decision, latency, n_judge, n_probe))
            continue
        for name in cfg["channels"]:
            res = channels[name].score(text)
            latency += res.latency_ms
            raw = np.array([res.raw_score])
            cal = calibrators.get(name)
            channel_scores[name] = float(cal.transform(raw)[0]) if cal else res.raw_score
        if cfg["fusion"] == "single":
            score = next(iter(channel_scores.values()))
            decision = Decision.BLOCK if score >= 0.5 else Decision.PASS
        elif cfg["fusion"] in ("mean", "max"):
            fuse = mean_fusion if cfg["fusion"] == "mean" else max_fusion
            decision = fuse(channel_scores)
            score = float(np.mean(list(channel_scores.values())))
        else:  # gate
            gd = gate.decide(channel_scores)
            decision = gd.decision
            if decision is Decision.ESCALATE and cfg["escalation"] != "none":
                assert judge_fn is not None
                jscore = judge_fn(text, rec.label)
                latency += SYNTH_JUDGE_LATENCY_MS
                n_judge = 1
                if cfg["escalation"] == "judge_probe":
                    latency += SYNTH_PROBE_LATENCY_MS
                    n_probe = settings.behavioural_probe_k
                    pscore = probe.score(text).raw_score
                    jscore = 0.7 * jscore + 0.3 * pscore
                score = effective_score(channel_scores, gd, escalation_score=jscore)
                decision = Decision.BLOCK if jscore >= 0.5 else Decision.PASS
            elif decision is Decision.ESCALATE:
                score = effective_score(channel_scores, gd)
                decision = Decision.BLOCK if score >= 0.5 else Decision.PASS
            else:
                score = effective_score(channel_scores, gd)
        _ = t0  # wall time kept per-channel above; judge/probe simulated
        rows.append(_row(rec, score, decision, latency, n_judge, n_probe))
    return pd.DataFrame(rows)


def _row(rec: Any, score: float, decision: Decision, latency: float,
         n_judge: int, n_probe: int) -> dict:
    return {
        "label": rec.label, "attack_family": rec.attack_family, "source": rec.source,
        "score": score, "decision": decision.value, "latency_ms": latency,
        "judge_calls": n_judge, "probe_calls": n_probe,
    }


def youden_threshold(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Operating threshold tuned on VALIDATION: max (TPR - FPR)."""
    from sklearn.metrics import roc_curve

    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    return float(thresholds[int(np.argmax(tpr - fpr))])


def summarise(cfg: dict, scores: pd.DataFrame, seed: int,
              threshold: float = 0.5) -> dict:
    """One ablation-table row for a configuration."""
    y = scores["label"].to_numpy()
    s = scores["score"].to_numpy()
    m = ev.detection_metrics(y, s, threshold=threshold)
    lo, hi = ev.bootstrap_auc_ci(y, s, n_resamples=1000, seed=seed)
    notinject = scores[scores["source"] == "synthetic_notinject"]
    notinject_fpr = (
        float((notinject["score"] >= threshold).mean()) if len(notinject) else float("nan")
    )
    judge_cost = (
        scores["judge_calls"].sum() * 0.004  # ~$0.004 per judged call (gpt-4o-mini class)
    )
    return {
        "config": cfg["name"],
        "threshold": threshold,
        **m,
        "roc_auc_ci_lo": lo, "roc_auc_ci_hi": hi,
        "notinject_fpr": notinject_fpr,
        "escalation_rate": float((scores["judge_calls"] > 0).mean()),
        "p95_latency_ms": ev.latency_percentiles(scores["latency_ms"].to_numpy())["p95"],
        "cost_per_1000_usd": float(judge_cost / max(1, len(scores)) * 1000),
        "n": len(scores),
    }


def run_all(settings: Settings, synthetic: bool, split: str = "test",
            n_trials: int = 50, out_dir: str = "results") -> pd.DataFrame:
    """Train, calibrate, tune the gate, run the grid, write CSVs."""
    from dgad.eval import datasets as ds

    root = Path(settings.data_dir) / "processed"
    if not (root / "train.csv").exists():
        ds.build(settings, synthetic=synthetic)
    train_df = pd.read_csv(root / "train.csv")
    val_df = pd.read_csv(root / "val.csv")
    eval_df = pd.read_csv(root / f"{split}.csv")

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    judge_fn = make_synthetic_judge(settings.random_seed) if synthetic else None

    # channels are trained once per "hardened" state, then shared across configs
    channels_plain = build_cheap_channels(settings, train_df, hardened=False)
    channels_hard = build_cheap_channels(settings, train_df, hardened=True)
    calibrators = fit_calibrators(channels_plain, val_df, settings)

    # persist trained heads + calibrators so the API boots trained
    channels_plain["statistical"].save(settings.models_dir)
    channels_plain["semantic"].save(settings.models_dir)
    for cal in calibrators.values():
        cal.save(settings.models_dir)

    # tune the gate on validation only, then freeze
    val_scores = []
    for rec in val_df.itertuples():
        per_ch = {}
        for name in ["statistical", "semantic"]:
            res = channels_plain[name].score(normalise(rec.text))
            per_ch[name] = float(calibrators[name].transform(np.array([res.raw_score]))[0])
        val_scores.append(per_ch)
    tuned = tune(val_scores, val_df["label"].tolist(), settings, n_trials=n_trials)
    gate = DisagreementGate(Settings(**tuned["best_params"]))
    pd.DataFrame(tuned["curve"]).to_csv(out / "gate_tradeoff_curve.csv", index=False)

    summary_rows = []
    for cfg in ABLATION_GRID:
        if synthetic and any(c.startswith("guard:") for c in cfg["channels"]):
            summary_rows.append({"config": cfg["name"],
                                 "skipped": "guard model requires download"})
            continue
        if any(c.startswith("guard:") for c in cfg["channels"]):
            raise RuntimeError(f"{cfg['name']}: guard-model configs need downloaded models")
        channels = channels_hard if cfg.get("hardened") else channels_plain
        cals = (fit_calibrators(channels, val_df, settings)
                if cfg.get("hardened") else calibrators)
        use_channels = {k: v for k, v in channels.items() if k in cfg["channels"]}
        # tune the operating threshold on VALIDATION, then freeze it
        val_scores = run_config(cfg, val_df, use_channels, cals, gate, judge_fn, settings)
        threshold = youden_threshold(val_scores["label"].to_numpy(),
                                     val_scores["score"].to_numpy())
        scores = run_config(cfg, eval_df, use_channels, cals, gate, judge_fn, settings)
        scores.to_csv(out / f"scores_{cfg['name']}.csv", index=False)
        summary_rows.append(summarise(cfg, scores, settings.random_seed,
                                      threshold=threshold))
        print(f"[{cfg['id']:>2}/12] {cfg['name']:<24} "
              f"roc_auc={summary_rows[-1].get('roc_auc', float('nan')):.4f}")

    table = pd.DataFrame(summary_rows)
    table.to_csv(out / "ablation.csv", index=False)
    (out / "run_meta.json").write_text(json.dumps({
        "split": split, "synthetic": synthetic, "seed": settings.random_seed,
        "gate_params": tuned["best_params"],
        "rows": {s: int(len(pd.read_csv(root / f"{s}.csv")))
                 for s in ["train", "val", "test", "holdout"]},
    }, indent=2))
    return table


def main() -> None:
    parser = argparse.ArgumentParser(description="DGAD ablation runner")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--holdout", action="store_true",
                        help="evaluate on the locked holdout split (final eval only)")
    parser.add_argument("--trials", type=int, default=50)
    args = parser.parse_args()
    if not args.all:
        parser.error("nothing to do: pass --all")
    split = "holdout" if args.holdout else "test"
    table = run_all(get_settings(), synthetic=args.synthetic, split=split,
                    n_trials=args.trials)
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(table.to_string(index=False))


if __name__ == "__main__":
    main()
