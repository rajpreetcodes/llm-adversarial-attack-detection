#!/usr/bin/env python3
"""Train DGAD channels on real datasets and run evaluation.

Usage:
    cd main
    HF_TOKEN=hf_... python train_real.py
"""

import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dgad.calibration import Calibrator
from dgad.channels.offset import OffsetChannel, heuristic_intent_extractor
from dgad.channels.semantic import SemanticChannel
from dgad.channels.statistical import StatisticalChannel
from dgad.config import Settings, get_settings
from dgad.eval import metrics as ev
from dgad.eval.runner import (
    ABLATION_GRID,
    fit_calibrators,
    run_config,
    summarise,
    youden_threshold,
)
from dgad.gate import DisagreementGate, tune
from dgad.normalise import normalise

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("train_real")

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data" / "processed"
RESULTS_DIR = ROOT / "results"
MODELS_DIR = ROOT / "models"

# Training subset sizes (CPU-friendly)
N_A = 3000   # Channel A rows (feature-only, fast)
N_B = 5000   # Channel B rows (SentenceTransformer is the bottleneck)


def main():
    settings = get_settings()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # --- Load splits ---
    train_df = pd.read_csv(DATA_DIR / "train.csv")
    val_df = pd.read_csv(DATA_DIR / "val.csv")
    test_df = pd.read_csv(DATA_DIR / "test.csv")
    logger.info("Splits: train=%d, val=%d, test=%d", len(train_df), len(val_df), len(test_df))

    texts_all = train_df["text"].tolist()
    labels_all = train_df["label"].tolist()
    rng = np.random.default_rng(settings.random_seed)

    # --- Train Channel A (statistical, feature-only) ---
    logger.info("=== Training Channel A (statistical, feature-only, %d rows) ===", N_A)
    t0 = time.perf_counter()
    idx_a = rng.choice(len(texts_all), min(N_A, len(texts_all)), replace=False)
    ch_a = StatisticalChannel(settings, use_model=False)
    ch_a.fit([texts_all[i] for i in idx_a], [labels_all[i] for i in idx_a])
    ch_a.save(settings.models_dir)
    logger.info("Channel A done in %.1fs", time.perf_counter() - t0)

    # --- Train Channel B (semantic, real embedder) ---
    logger.info("=== Training Channel B (semantic, %d rows) ===", N_B)
    t0 = time.perf_counter()
    idx_b = rng.choice(len(texts_all), min(N_B, len(texts_all)), replace=False)
    ch_b = SemanticChannel(settings)
    ch_b.fit([texts_all[i] for i in idx_b], [labels_all[i] for i in idx_b])
    ch_b.save(settings.models_dir)
    logger.info("Channel B done in %.1fs", time.perf_counter() - t0)

    # --- Channel E (offset, no training needed) ---
    logger.info("=== Instantiating Channel E (offset) ===")
    ch_e = OffsetChannel(settings, extractor=heuristic_intent_extractor)
    channels = {"statistical": ch_a, "semantic": ch_b, "offset": ch_e}

    # --- Calibrate on validation ---
    logger.info("=== Fitting calibrators on %d validation rows ===", len(val_df))
    t0 = time.perf_counter()
    calibrators = fit_calibrators(channels, val_df, settings)
    for name, cal in calibrators.items():
        cal.save(settings.models_dir)
    logger.info("Calibrators done in %.1fs", time.perf_counter() - t0)

    # --- Tune gate on validation ---
    logger.info("=== Tuning disagreement gate ===")
    t0 = time.perf_counter()
    val_scores = []
    for rec in val_df.itertuples():
        per_ch = {}
        for name in ["statistical", "semantic"]:
            res = channels[name].score(normalise(rec.text))
            cal = calibrators.get(name)
            per_ch[name] = float(cal.transform(np.array([res.raw_score]))[0]) if cal else res.raw_score
        val_scores.append(per_ch)
    tuned = tune(val_scores, val_df["label"].tolist(), settings, n_trials=50)
    gate = DisagreementGate(Settings(**tuned["best_params"]))
    logger.info("Gate tuned in %.1fs: %s", time.perf_counter() - t0, tuned["best_params"])
    pd.DataFrame(tuned["curve"]).to_csv(RESULTS_DIR / "gate_tradeoff_curve.csv", index=False)

    # --- Run ablation ---
    logger.info("=== Running ablation grid ===")
    summary_rows = []
    for cfg in ABLATION_GRID:
        name = cfg["name"]
        if any(c.startswith("guard:") for c in cfg["channels"]):
            summary_rows.append({"config": name, "skipped": "guard model"})
            continue
        if cfg["channels"] == ["judge"]:
            summary_rows.append({"config": name, "skipped": "judge needs API"})
            continue
        use_ch = {k: v for k, v in channels.items() if k in cfg["channels"]}
        if not use_ch:
            summary_rows.append({"config": name, "skipped": "no channels"})
            continue
        use_cals = {k: v for k, v in calibrators.items() if k in cfg["channels"]}
        try:
            val_sc = run_config(cfg, val_df, use_ch, use_cals, gate, None, settings)
            thr = youden_threshold(val_sc["label"].to_numpy(), val_sc["score"].to_numpy())
            scores = run_config(cfg, test_df, use_ch, use_cals, gate, None, settings)
            scores.to_csv(RESULTS_DIR / f"scores_{name}.csv", index=False)
            row = summarise(cfg, scores, settings.random_seed, threshold=thr)
            summary_rows.append(row)
            logger.info("  [%2d/12] %-24s AUC=%.4f  F1=%.4f  FPR=%.4f",
                        cfg["id"], name, row.get("roc_auc", float("nan")),
                        row.get("f1", float("nan")), row.get("fpr", float("nan")))
        except Exception as exc:
            logger.error("  [%s] FAILED: %s", name, exc)
            summary_rows.append({"config": name, "error": str(exc)[:200]})

    table = pd.DataFrame(summary_rows)
    table.to_csv(RESULTS_DIR / "ablation.csv", index=False)

    # --- Save metadata ---
    meta = {
        "split": "test", "synthetic": False, "seed": settings.random_seed,
        "gate_params": tuned["best_params"],
        "rows": {"train": len(train_df), "val": len(val_df), "test": len(test_df)},
    }
    (RESULTS_DIR / "run_meta.json").write_text(json.dumps(meta, indent=2))

    # --- Print results ---
    print("\n" + "=" * 90)
    print("DGAD ABLATION RESULTS (REAL DATA)")
    print("=" * 90)
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(table.to_string(index=False))
    print(f"\nResults: {RESULTS_DIR}/")
    print(f"Models:  {MODELS_DIR}/")


if __name__ == "__main__":
    main()
