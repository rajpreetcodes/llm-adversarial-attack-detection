#!/usr/bin/env python3
"""Step 1: Train channels + calibrators + tune gate on real data."""
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))
from dgad.calibration import Calibrator, expected_calibration_error, reliability_diagram
from dgad.channels.offset import OffsetChannel, heuristic_intent_extractor
from dgad.channels.semantic import SemanticChannel
from dgad.channels.statistical import StatisticalChannel
from dgad.config import get_settings
from dgad.gate import tune
from dgad.normalise import normalise

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("train")

ROOT = Path(__file__).parent
DATA = ROOT / "data/processed"
MODELS = ROOT / "models"
RESULTS = ROOT / "results"


def batch_raw_scores(channels, texts):
    """Score validation prompts in batches so MiniLM is not invoked per row."""
    from dgad.channels.offset import _cosine_distance

    scores = {}
    scores["statistical"] = np.array([
        channels["statistical"].score(text).raw_score for text in texts
    ])

    semantic = channels["semantic"]
    semantic_embeddings = semantic._encode(texts)
    if semantic._head is None:
        raise RuntimeError("semantic head was not fitted")
    scores["semantic"] = semantic._head.predict_proba(semantic_embeddings)[:, 1]

    offset = channels["offset"]
    intents = [heuristic_intent_extractor(text) for text in texts]
    # Channel B and E use the same configured MiniLM model. Reuse the prompt
    # embeddings above and encode only the extracted intents.
    intent_embeddings = offset._encode(intents)
    scores["offset"] = np.array([
        np.clip(_cosine_distance(prompt, intent), 0.0, 1.0)
        for prompt, intent in zip(semantic_embeddings, intent_embeddings, strict=True)
    ])
    return scores

def main():
    s = get_settings()
    train = pd.read_csv(DATA / "train.csv")
    val = pd.read_csv(DATA / "val.csv")
    log.info("Train=%d  Val=%d", len(train), len(val))

    tx = [normalise(text) for text in train["text"].tolist()]
    ly = train["label"].tolist()
    vx = [normalise(text) for text in val["text"].tolist()]
    vy = val["label"].to_numpy()
    rng = np.random.default_rng(s.random_seed)

    # Channel A (feature-only, fast)
    t0 = time.perf_counter()
    idx = rng.choice(len(tx), min(3000, len(tx)), replace=False)
    ch_a = StatisticalChannel(s, use_model=False)
    ch_a.fit([tx[i] for i in idx], [ly[i] for i in idx])
    ch_a.save(s.models_dir)
    log.info("Ch A: %.1fs", time.perf_counter()-t0)

    # Channel B (semantic, real embedder)
    t0 = time.perf_counter()
    idx = rng.choice(len(tx), min(3000, len(tx)), replace=False)
    ch_b = SemanticChannel(s)
    ch_b.fit([tx[i] for i in idx], [ly[i] for i in idx])
    ch_b.save(s.models_dir)
    log.info("Ch B: %.1fs", time.perf_counter()-t0)

    # Channel E (offset, no training)
    ch_e = OffsetChannel(s, extractor=heuristic_intent_extractor)
    channels = {"statistical": ch_a, "semantic": ch_b, "offset": ch_e}

    # Calibrate. Batch MiniLM inference is over 100x faster than one-row calls.
    t0 = time.perf_counter()
    raw = batch_raw_scores(channels, vx)
    cals = {}
    calibration_metrics = {}
    for name, raw_scores in raw.items():
        cal = Calibrator(name, settings=s).fit(raw_scores, vy)
        after = cal.transform(raw_scores)
        cals[name] = cal
        cal.save(s.models_dir)
        calibration_metrics[name] = {
            "ece_before": expected_calibration_error(raw_scores, vy),
            "ece_after": expected_calibration_error(after, vy),
        }
        reliability_diagram(
            raw_scores, after, vy, f"{name.title()} channel calibration",
            RESULTS / "figures" / f"calibration_{name}.png",
        )
    log.info("Calibrators: %.1fs", time.perf_counter()-t0)

    # Tune gate (quick: 30 trials)
    t0 = time.perf_counter()
    calibrated = {name: cal.transform(raw[name]) for name, cal in cals.items()}
    vscores = [
        {"statistical": float(calibrated["statistical"][i]),
         "semantic": float(calibrated["semantic"][i])}
        for i in range(len(val))
    ]
    tuned = tune(vscores, val["label"].tolist(), s, n_trials=30)
    best = tuned["best_params"]
    gate_params = {
        "gate_t_low": best["t_low"],
        "gate_t_high": best["t_high"],
        "gate_t_d": best["t_d"],
    }
    log.info("Gate: %.1fs params=%s", time.perf_counter()-t0, tuned["best_params"])

    # Save everything
    RESULTS.mkdir(exist_ok=True)
    pd.DataFrame(tuned["curve"]).to_csv(RESULTS / "gate_tradeoff_curve.csv", index=False)
    funnel = json.loads((DATA / "funnel.json").read_text())
    meta = {
        "gate_params": gate_params,
        "seed": s.random_seed,
        "train": len(train),
        "val": len(val),
        "training_rows_per_channel": {
            "statistical": int(len(idx)),
            "semantic": int(len(idx)),
        },
        "channel_a_mode": "features",
        "channel_b_embedder": s.embedding_model,
        "calibration_method": s.calibration_method,
        "calibration": calibration_metrics,
        "dataset_funnel": funnel,
        "source_counts": train["source"].value_counts().to_dict(),
        "family_counts": train["attack_family"].value_counts().to_dict(),
    }
    (RESULTS / "train_meta.json").write_text(json.dumps(meta, indent=2))
    log.info("DONE — all models saved to %s", MODELS)

if __name__ == "__main__":
    main()
