#!/usr/bin/env python3
"""Step 1: Train channels + calibrators + tune gate on real data."""
import json, logging, sys, time
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))
from dgad.calibration import Calibrator
from dgad.channels.offset import OffsetChannel, heuristic_intent_extractor
from dgad.channels.semantic import SemanticChannel
from dgad.channels.statistical import StatisticalChannel
from dgad.config import Settings, get_settings
from dgad.eval.runner import fit_calibrators
from dgad.gate import DisagreementGate, tune
from dgad.normalise import normalise

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("train")

ROOT = Path(__file__).parent
DATA = ROOT / "data/processed"
MODELS = ROOT / "models"

def main():
    s = get_settings()
    train = pd.read_csv(DATA / "train.csv")
    val = pd.read_csv(DATA / "val.csv")
    log.info("Train=%d  Val=%d", len(train), len(val))

    tx, ly = train["text"].tolist(), train["label"].tolist()
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

    # Calibrate
    t0 = time.perf_counter()
    cals = fit_calibrators(channels, val, s)
    for n, c in cals.items(): c.save(s.models_dir)
    log.info("Calibrators: %.1fs", time.perf_counter()-t0)

    # Tune gate (quick: 30 trials)
    t0 = time.perf_counter()
    vscores = []
    for rec in val.itertuples():
        pc = {}
        for n in ["statistical","semantic"]:
            r = channels[n].score(normalise(rec.text))
            pc[n] = float(cals[n].transform(np.array([r.raw_score]))[0]) if n in cals else r.raw_score
        vscores.append(pc)
    tuned = tune(vscores, val["label"].tolist(), s, n_trials=30)
    gate = DisagreementGate(Settings(**tuned["best_params"]))
    log.info("Gate: %.1fs params=%s", time.perf_counter()-t0, tuned["best_params"])

    # Save everything
    (ROOT/"results").mkdir(exist_ok=True)
    pd.DataFrame(tuned["curve"]).to_csv(ROOT/"results/gate_tradeoff_curve.csv")
    meta = {"gate_params": tuned["best_params"], "train": len(train), "val": len(val)}
    (ROOT/"results/train_meta.json").write_text(json.dumps(meta, indent=2))
    log.info("DONE — all models saved to %s", MODELS)

if __name__ == "__main__":
    main()
