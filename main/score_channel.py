#!/usr/bin/env python3
"""Score ONE channel and save to cache. Usage: python score_channel.py <channel>

Channels: a, b, e
"""
import json, logging, sys, time
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))
from dgad.normalise import normalise
from dgad.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("score")

ROOT = Path(__file__).parent
DATA = ROOT / "data/processed"
RESULTS = ROOT / "results"
MODELS = ROOT / "models"
CACHE = RESULTS / "scores_cache.npz"

CHANNEL = sys.argv[1] if len(sys.argv) > 1 else "a"


def load_texts(split):
    df = pd.read_csv(DATA / f"{split}.csv")
    return [normalise(t) for t in df["text"].tolist()]


def main():
    RESULTS.mkdir(exist_ok=True)
    s = get_settings()

    val_texts = load_texts("val")
    test_texts = load_texts("test")
    all_texts = val_texts + test_texts
    n_val, n_test = len(val_texts), len(test_texts)

    t_start = time.perf_counter()

    if CHANNEL == "a":
        from dgad.channels.statistical import anomaly_features
        import joblib
        rows_v = np.array([anomaly_features(t) for t in val_texts])
        rows_t = np.array([anomaly_features(t) for t in test_texts])
        combiner_path = MODELS / "channel_a_combiner.joblib"
        if combiner_path.exists():
            combiner = joblib.load(combiner_path)
            feat_v = np.column_stack([np.zeros(n_val), rows_v])
            feat_t = np.column_stack([np.zeros(n_test), rows_t])
            raw_v = combiner.predict_proba(feat_v)[:, 1]
            raw_t = combiner.predict_proba(feat_t)[:, 1]
        else:
            raw_v = np.zeros(n_val)
            raw_t = np.zeros(n_test)

        # Apply calibrator
        cal_path = MODELS / "calibrator_statistical_platt.joblib"
        if cal_path.exists():
            from dgad.calibration import Calibrator
            cal = Calibrator.load(cal_path)
            raw_v = cal.transform(raw_v.reshape(-1, 1)).flatten()
            raw_t = cal.transform(raw_t.reshape(-1, 1)).flatten()

        _save("statistical", raw_v, raw_t)

    elif CHANNEL == "b":
        import joblib
        from sentence_transformers import SentenceTransformer
        head = joblib.load(MODELS / "channel_b_head.joblib")
        log.info("Loading embedder...")
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        log.info("Embedder loaded")

        chunk = 500
        scores_v = np.zeros(n_val)
        for i in range(0, n_val, chunk):
            j = min(i + chunk, n_val)
            emb = model.encode(val_texts[i:j], batch_size=256, show_progress_bar=False, convert_to_numpy=True)
            scores_v[i:j] = head.predict_proba(emb)[:, 1]
            log.info("  Val: %d/%d", j, n_val)

        scores_t = np.zeros(n_test)
        for i in range(0, n_test, chunk):
            j = min(i + chunk, n_test)
            emb = model.encode(test_texts[i:j], batch_size=256, show_progress_bar=False, convert_to_numpy=True)
            scores_t[i:j] = head.predict_proba(emb)[:, 1]
            log.info("  Test: %d/%d", j, n_test)

        # Calibrate
        cal_path = MODELS / "calibrator_semantic_platt.joblib"
        if cal_path.exists():
            from dgad.calibration import Calibrator
            cal = Calibrator.load(cal_path)
            scores_v = cal.transform(scores_v.reshape(-1, 1)).flatten()
            scores_t = cal.transform(scores_t.reshape(-1, 1)).flatten()

        _save("semantic", scores_v, scores_t)

    elif CHANNEL == "e":
        from sentence_transformers import SentenceTransformer
        from dgad.channels.offset import heuristic_intent_extractor
        log.info("Loading embedder...")
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        log.info("Embedder loaded")

        chunk = 300
        scores_v = np.zeros(n_val)
        for i in range(0, n_val, chunk):
            j = min(i + chunk, n_val)
            texts = val_texts[i:j]
            intents = [heuristic_intent_extractor(t) for t in texts]
            embs = model.encode(texts + intents, batch_size=256, show_progress_bar=False, convert_to_numpy=True)
            orig = embs[:len(texts)]
            intn = embs[len(texts):]
            cos = np.sum(orig * intn, axis=1) / (np.linalg.norm(orig, axis=1) * np.linalg.norm(intn, axis=1) + 1e-8)
            scores_v[i:j] = 1.0 - cos
            log.info("  Val: %d/%d", j, n_val)

        scores_t = np.zeros(n_test)
        for i in range(0, n_test, chunk):
            j = min(i + chunk, n_test)
            texts = test_texts[i:j]
            intents = [heuristic_intent_extractor(t) for t in texts]
            embs = model.encode(texts + intents, batch_size=256, show_progress_bar=False, convert_to_numpy=True)
            orig = embs[:len(texts)]
            intn = embs[len(texts):]
            cos = np.sum(orig * intn, axis=1) / (np.linalg.norm(orig, axis=1) * np.linalg.norm(intn, axis=1) + 1e-8)
            scores_t[i:j] = 1.0 - cos
            log.info("  Test: %d/%d", j, n_test)

        # Calibrate
        cal_path = MODELS / "calibrator_offset_platt.joblib"
        if cal_path.exists():
            from dgad.calibration import Calibrator
            cal = Calibrator.load(cal_path)
            scores_v = cal.transform(scores_v.reshape(-1, 1)).flatten()
            scores_t = cal.transform(scores_t.reshape(-1, 1)).flatten()

        _save("offset", scores_v, scores_t)

    log.info("Done in %.1fs", time.perf_counter() - t_start)


def _save(name, val_scores, test_scores):
    """Save scores to cache, merging with existing cache."""
    if CACHE.exists():
        data = dict(np.load(CACHE))
    else:
        data = {}
    data[f"val_{name}"] = val_scores
    data[f"test_{name}"] = test_scores
    np.savez_compressed(CACHE, **data)
    log.info("Saved %s to cache (%s)", name, CACHE)


if __name__ == "__main__":
    main()
