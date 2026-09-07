#!/usr/bin/env python3
"""Step 2: Cached batch evaluation — scores are saved incrementally.

Strategy:
1. Score Channel A (fast, ~1s)
2. Score Channel B (batched embeddings, ~4min)
3. Score Channel E (batched embeddings, ~10min)
4. All scores cached to scores_cache.npz — resume if interrupted
5. Run ablation from cache
"""
import json, logging, sys, time
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))
from dgad.calibration import Calibrator
from dgad.channels.offset import heuristic_intent_extractor
from dgad.channels.statistical import anomaly_features
from dgad.config import Settings, get_settings
from dgad.eval import metrics as ev
from dgad.gate import DisagreementGate
from dgad.normalise import normalise
from dgad.schemas import Decision

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("eval")

ROOT = Path(__file__).parent
DATA = ROOT / "data/processed"
RESULTS = ROOT / "results"
MODELS = ROOT / "models"
CACHE = RESULTS / "scores_cache.npz"

ABLATION_GRID = [
    {"id": 1,  "name": "channel_a_only",       "channels": ["statistical"], "fusion": "single"},
    {"id": 2,  "name": "channel_b_only",        "channels": ["semantic"],    "fusion": "single"},
    {"id": 6,  "name": "naive_mean_fusion",     "channels": ["statistical", "semantic"], "fusion": "mean"},
    {"id": 7,  "name": "naive_max_fusion",      "channels": ["statistical", "semantic"], "fusion": "max"},
    {"id": 8,  "name": "dgad_no_escalation",    "channels": ["statistical", "semantic"], "fusion": "gate"},
    {"id": 10, "name": "dgad_offset",           "channels": ["statistical", "semantic", "offset"], "fusion": "gate"},
    {"id": 11, "name": "dgad_full",             "channels": ["statistical", "semantic", "offset"], "fusion": "gate"},
]


def youden_threshold(y_true, y_score):
    from sklearn.metrics import roc_curve
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    return float(thresholds[int(np.argmax(tpr - fpr))])


def batch_channel_a(texts):
    rows = np.array([anomaly_features(t) for t in texts])
    combiner_path = MODELS / "channel_a_combiner.joblib"
    if combiner_path.exists():
        import joblib
        combiner = joblib.load(combiner_path)
        feature_matrix = np.column_stack([np.zeros(len(texts)), rows])
        raw = combiner.predict_proba(feature_matrix)[:, 1]
    else:
        feats = rows
        anomaly = np.clip(
            feats[:, 0] + feats[:, 1] + np.minimum(feats[:, 2], 5) / 5
            + feats[:, 3] + feats[:, 4], 0, 3
        ) / 3
        raw = 0.3 * anomaly
    return raw.astype(float)


def score_channel_b_chunked(texts, embedder, chunk_size=500):
    """Score Channel B in chunks, returning full array."""
    import joblib
    head = joblib.load(MODELS / "channel_b_head.joblib")
    n = len(texts)
    result = np.zeros(n)
    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        chunk = texts[start:end]
        emb = embedder(chunk)
        result[start:end] = head.predict_proba(emb)[:, 1]
        log.info("    Ch B: %d/%d done", end, n)
    return result.astype(float)


def score_channel_e_chunked(texts, embedder, chunk_size=300):
    """Score Channel E in chunks — encode texts+intents together per chunk."""
    n = len(texts)
    result = np.zeros(n)
    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        chunk = texts[start:end]
        intents = [heuristic_intent_extractor(t) for t in chunk]
        combined = chunk + intents
        embs = embedder(combined)
        orig_emb = embs[:len(chunk)]
        intent_emb = embs[len(chunk):]
        cos_sim = np.sum(orig_emb * intent_emb, axis=1) / (
            np.linalg.norm(orig_emb, axis=1) * np.linalg.norm(intent_emb, axis=1) + 1e-8
        )
        result[start:end] = 1.0 - cos_sim
        log.info("    Ch E: %d/%d done", end, n)
    return result.astype(float)


def run_ablation(all_scores_val, all_scores_test, y_val, y_test, gate):
    summary_rows = []
    for cfg in ABLATION_GRID:
        name = cfg["name"]
        ch_names = cfg["channels"]

        val_dict = {k: all_scores_val[k] for k in ch_names}
        test_dict = {k: all_scores_test[k] for k in ch_names}

        if cfg["fusion"] == "single":
            val_combined = list(val_dict.values())[0]
            test_combined = list(test_dict.values())[0]
        elif cfg["fusion"] == "mean":
            val_combined = np.mean(list(val_dict.values()), axis=0)
            test_combined = np.mean(list(test_dict.values()), axis=0)
        elif cfg["fusion"] == "max":
            val_combined = np.max(list(val_dict.values()), axis=0)
            test_combined = np.max(list(test_dict.values()), axis=0)
        elif cfg["fusion"] == "gate":
            keys = list(val_dict.keys())
            val_arr = np.column_stack([val_dict[k] for k in keys])
            test_arr = np.column_stack([test_dict[k] for k in keys])

            def gate_score_vec(arr):
                results = np.full(len(arr), 0.5)
                for i in range(len(arr)):
                    d = {k: float(arr[i, j]) for j, k in enumerate(keys)}
                    gd = gate.decide(d)
                    if gd.decision is not Decision.ESCALATE:
                        results[i] = float(np.mean(list(d.values())))
                return results

            val_combined = gate_score_vec(val_arr)
            test_combined = gate_score_vec(test_arr)
        else:
            val_combined = np.mean(list(val_dict.values()), axis=0)
            test_combined = np.mean(list(test_dict.values()), axis=0)

        thr = youden_threshold(y_val, val_combined)
        m = ev.detection_metrics(y_test, test_combined, threshold=thr)
        lo, hi = ev.bootstrap_auc_ci(y_test, test_combined, n_resamples=1000, seed=42)
        row = {
            "config": name, "threshold": thr, **m,
            "roc_auc_ci_lo": lo, "roc_auc_ci_hi": hi,
            "n": len(y_test),
        }
        summary_rows.append(row)
        log.info("  %-24s AUC=%.4f  F1=%.4f  FPR=%.4f  Prec=%.4f  Rec=%.4f",
                name, m.get("roc_auc", float("nan")), m.get("f1", float("nan")),
                m.get("fpr", float("nan")), m.get("precision", float("nan")),
                m.get("recall", float("nan")))

    return pd.DataFrame(summary_rows)


def main():
    s = get_settings()
    RESULTS.mkdir(exist_ok=True)
    t_start = time.perf_counter()

    # Check for --ablation-only flag (skip scoring, use cache)
    ablation_only = "--ablation-only" in sys.argv

    val_df = pd.read_csv(DATA / "val.csv")
    test_df = pd.read_csv(DATA / "test.csv")
    val_texts = [normalise(t) for t in val_df["text"].tolist()]
    test_texts = [normalise(t) for t in test_df["text"].tolist()]
    y_val = val_df["label"].to_numpy()
    y_test = test_df["label"].to_numpy()
    log.info("Val=%d  Test=%d", len(val_df), len(test_df))

    # Gate
    meta_path = RESULTS / "train_meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        gate = DisagreementGate(Settings(**meta["gate_params"]))
    else:
        gate = DisagreementGate(s)

    # Calibrators
    calibrators = {}
    for name in ["statistical", "semantic", "offset"]:
        path = MODELS / f"calibrator_{name}_platt.joblib"
        if path.exists():
            calibrators[name] = Calibrator.load(path)

    # ===== SCORING (or load from cache) =====
    if ablation_only and CACHE.exists():
        log.info("Loading scores from cache: %s", CACHE)
        data = np.load(CACHE)
        all_scores_val = {
            "statistical": data["val_statistical"],
            "semantic": data["val_semantic"],
            "offset": data["val_offset"],
        }
        all_scores_test = {
            "statistical": data["test_statistical"],
            "semantic": data["test_semantic"],
            "offset": data["test_offset"],
        }
    else:
        # Channel A
        if not CACHE.exists() or "val_statistical" not in np.load(CACHE, allow_pickle=True).files:
            log.info("Scoring Channel A...")
            t0 = time.perf_counter()
            raw_a_val = batch_channel_a(val_texts)
            raw_a_test = batch_channel_a(test_texts)
            cal_a = calibrators.get("statistical")
            scores_a_val = cal_a.transform(raw_a_val.reshape(-1, 1)).flatten() if cal_a else raw_a_val
            scores_a_test = cal_a.transform(raw_a_test.reshape(-1, 1)).flatten() if cal_a else raw_a_test
            log.info("  Ch A done in %.1fs", time.perf_counter() - t0)

            # Save partial cache
            np.savez_compressed(CACHE,
                val_statistical=scores_a_val, val_semantic=np.zeros(1), val_offset=np.zeros(1),
                test_statistical=scores_a_test, test_semantic=np.zeros(1), test_offset=np.zeros(1))
        else:
            data = np.load(CACHE)
            scores_a_val = data["val_statistical"]
            scores_a_test = data["test_statistical"]
            log.info("Channel A loaded from cache")

        # Channel B
        if "val_semantic" not in np.load(CACHE, allow_pickle=True).files or np.load(CACHE)["val_semantic"].sum() == 0:
            log.info("Scoring Channel B (chunked embeddings)...")
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            def embed(texts):
                return np.asarray(model.encode(texts, batch_size=256, show_progress_bar=False, convert_to_numpy=True), dtype=float)

            t0 = time.perf_counter()
            scores_b_val = score_channel_b_chunked(val_texts, embed, chunk_size=500)
            scores_b_test = score_channel_b_chunked(test_texts, embed, chunk_size=500)
            cal_b = calibrators.get("semantic")
            scores_b_val = cal_b.transform(scores_b_val.reshape(-1, 1)).flatten() if cal_b else scores_b_val
            scores_b_test = cal_b.transform(scores_b_test.reshape(-1, 1)).flatten() if cal_b else scores_b_test
            log.info("  Ch B done in %.1fs", time.perf_counter() - t0)

            # Save partial cache
            np.savez_compressed(CACHE,
                val_statistical=scores_a_val, val_semantic=scores_b_val, val_offset=np.zeros(1),
                test_statistical=scores_a_test, test_semantic=scores_b_test, test_offset=np.zeros(1))
        else:
            data = np.load(CACHE)
            scores_b_val = data["val_semantic"]
            scores_b_test = data["test_semantic"]
            log.info("Channel B loaded from cache")

        # Channel E
        if "val_offset" not in np.load(CACHE, allow_pickle=True).files or np.load(CACHE)["val_offset"].sum() == 0:
            log.info("Scoring Channel E (chunked offset embeddings)...")
            t0 = time.perf_counter()
            scores_e_val = score_channel_e_chunked(val_texts, embed, chunk_size=300)
            scores_e_test = score_channel_e_chunked(test_texts, embed, chunk_size=300)
            cal_e = calibrators.get("offset")
            scores_e_val = cal_e.transform(scores_e_val.reshape(-1, 1)).flatten() if cal_e else scores_e_val
            scores_e_test = cal_e.transform(scores_e_test.reshape(-1, 1)).flatten() if cal_e else scores_e_test
            log.info("  Ch E done in %.1fs", time.perf_counter() - t0)

            # Save complete cache
            np.savez_compressed(CACHE,
                val_statistical=scores_a_val, val_semantic=scores_b_val, val_offset=scores_e_val,
                test_statistical=scores_a_test, test_semantic=scores_b_test, test_offset=scores_e_test)
        else:
            data = np.load(CACHE)
            scores_e_val = data["val_offset"]
            scores_e_test = data["test_offset"]
            log.info("Channel E loaded from cache")

        all_scores_val = {"statistical": scores_a_val, "semantic": scores_b_val, "offset": scores_e_val}
        all_scores_test = {"statistical": scores_a_test, "semantic": scores_b_test, "offset": scores_e_test}

    total_score_time = time.perf_counter() - t_start
    log.info("Scoring phase done in %.1fs", total_score_time)

    # ===== ABLATION =====
    log.info("Running ablation...")
    table = run_ablation(all_scores_val, all_scores_test, y_val, y_test, gate)
    table.to_csv(RESULTS / "ablation.csv", index=False)

    meta = {
        "split": "test", "synthetic": False, "seed": 42,
        "rows": {"val": len(val_df), "test": len(test_df)},
        "total_time_s": round(time.perf_counter() - t_start, 1),
    }
    (RESULTS / "run_meta.json").write_text(json.dumps(meta, indent=2))

    print("\n" + "=" * 90)
    print("DGAD ABLATION RESULTS (REAL DATA)")
    print("=" * 90)
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(table.to_string(index=False))
    print(f"\nTotal time: {time.perf_counter()-t_start:.1f}s")


if __name__ == "__main__":
    main()
