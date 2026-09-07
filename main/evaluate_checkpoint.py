#!/usr/bin/env python3
"""Evaluate the trained checkpoint on test data without claiming C/D results."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dgad.calibration import Calibrator
from dgad.channels.offset import OffsetChannel, heuristic_intent_extractor
from dgad.channels.semantic import SemanticChannel
from dgad.channels.statistical import StatisticalChannel
from dgad.config import Settings
from dgad.eval.metrics import bootstrap_auc_ci, detection_metrics
from dgad.gate import DisagreementGate
from dgad.normalise import normalise
from dgad.schemas import Decision
from train_step1 import batch_raw_scores

ROOT = Path(__file__).parent


def main() -> None:
    meta = json.loads((ROOT / "results/train_meta.json").read_text())
    settings = Settings(**meta["gate_params"])
    test = pd.read_csv(ROOT / "data/processed/test.csv")
    texts = [normalise(text) for text in test["text"].tolist()]
    labels = test["label"].to_numpy()

    channels = {
        "statistical": StatisticalChannel(settings, use_model=False).load(settings.models_dir),
        "semantic": SemanticChannel(settings).load(settings.models_dir),
        "offset": OffsetChannel(settings, extractor=heuristic_intent_extractor),
    }
    raw = batch_raw_scores(channels, texts)
    calibrated = {
        name: Calibrator.load(
            ROOT / settings.models_dir / f"calibrator_{name}_{settings.calibration_method}.joblib"
        ).transform(values)
        for name, values in raw.items()
    }

    gate = DisagreementGate(settings)
    gate_decisions = [
        gate.decide({"statistical": float(a), "semantic": float(b)})
        for a, b in zip(calibrated["statistical"], calibrated["semantic"], strict=True)
    ]
    # Ranking score remains the calibrated A/B mean. Escalated samples are left
    # unresolved here because this checkpoint evaluator makes no C/D claim.
    scores = {
        "channel_a_features": calibrated["statistical"],
        "channel_b_minilm": calibrated["semantic"],
        "naive_mean_ab": (calibrated["statistical"] + calibrated["semantic"]) / 2,
        "naive_max_ab": np.maximum(calibrated["statistical"], calibrated["semantic"]),
    }
    rows = []
    for name, values in scores.items():
        lo, hi = bootstrap_auc_ci(labels, values, n_resamples=1000, seed=settings.random_seed)
        result = {"configuration": name, **detection_metrics(labels, values)}
        result.update({"roc_auc_ci_lo": lo, "roc_auc_ci_hi": hi, "n": len(test)})
        notinject = test["source"].eq("notinject").to_numpy()
        result["notinject_fpr"] = float((values[notinject] >= 0.5).mean())
        result["escalation_rate"] = (
            float(np.mean([d.decision is Decision.ESCALATE for d in gate_decisions]))
            if name == "naive_mean_ab" else np.nan
        )
        rows.append(result)

    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "checkpoint_metrics.csv", index=False)
    pd.DataFrame({
        "label": labels,
        "attack_family": test["attack_family"],
        "source": test["source"],
        **scores,
        "gate_decision": [d.decision.value for d in gate_decisions],
        "disagreement": [d.disagreement for d in gate_decisions],
    }).to_csv(out / "checkpoint_scores.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
