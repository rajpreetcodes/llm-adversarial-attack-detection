"""Tests for eval metrics."""

import numpy as np
import pandas as pd
import pytest
from sklearn import metrics as skm

from dgad.eval import metrics as ev


def test_detection_metrics_match_sklearn():
    rng = np.random.default_rng(0)
    y = (rng.random(300) < 0.5).astype(int)
    s = np.clip(y * 0.6 + rng.normal(0, 0.3, 300), 0, 1)
    m = ev.detection_metrics(y, s)
    assert m["roc_auc"] == pytest.approx(skm.roc_auc_score(y, s))
    assert m["fpr"] == pytest.approx(
        skm.confusion_matrix(y, (s >= 0.5).astype(int), labels=[0, 1])[0, 1]
        / max(1, (y == 0).sum()))


def test_bootstrap_ci_contains_point_estimate():
    rng = np.random.default_rng(1)
    y = (rng.random(400) < 0.5).astype(int)
    s = np.clip(y + rng.normal(0, 0.5, 400), 0, 1)
    lo, hi = ev.bootstrap_auc_ci(y, s, n_resamples=200)
    auc = skm.roc_auc_score(y, s)
    assert lo <= auc <= hi
    assert lo < hi


def test_per_family():
    df = pd.DataFrame({
        "label": [0, 0, 1, 1, 0, 1],
        "attack_family": ["a", "a", "a", "a", "b", "b"],
        "score": [0.1, 0.2, 0.8, 0.9, 0.4, 0.6],
    })
    out = ev.per_family(df)
    assert set(out["attack_family"]) == {"a", "b"}
    assert out.loc[out["attack_family"] == "a", "roc_auc"].iloc[0] == pytest.approx(1.0)


def test_latency_percentiles():
    arr = np.arange(1, 101)
    p = ev.latency_percentiles(arr)
    assert p["p50"] == pytest.approx(50.5)
    assert p["p95"] > p["p50"]


def test_cost_per_1000():
    assert ev.cost_per_1000(1000, 100, 0.004) == pytest.approx(0.4)
    assert ev.cost_per_1000(0, 0, 0.004) == 0.0
