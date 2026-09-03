"""Exhaustive tests for the disagreement gate (pure logic, core novelty)."""

import numpy as np
import pytest
from hypothesis import given
from hypothesis import settings as hyp_settings
from hypothesis import strategies as st

from dgad.config import Settings
from dgad.gate import (
    DisagreementGate,
    disagreement,
    effective_score,
    max_fusion,
    mean_fusion,
    tune,
)
from dgad.schemas import Decision

score_dicts = st.dictionaries(
    keys=st.sampled_from(["a", "b", "e"]),
    values=st.floats(min_value=0.0, max_value=1.0),
    min_size=2,
    max_size=3,
)


@given(scores=score_dicts)
@hyp_settings(max_examples=200)
def test_decision_is_always_valid(scores):
    gate = DisagreementGate(Settings())
    out = gate.decide(scores)
    assert out.decision in Decision
    assert out.scores == scores


@given(scores=score_dicts)
@hyp_settings(max_examples=100)
def test_deterministic(scores):
    gate = DisagreementGate(Settings())
    assert gate.decide(scores) == gate.decide(scores)


def test_all_low_passes():
    gate = DisagreementGate(Settings())
    assert gate.decide({"a": 0.0, "b": 0.05}).decision is Decision.PASS


def test_all_high_blocks():
    gate = DisagreementGate(Settings())
    assert gate.decide({"a": 0.99, "b": 0.8}).decision is Decision.BLOCK


def test_clear_disagreement_escalates():
    gate = DisagreementGate(Settings())
    assert gate.decide({"a": 0.1, "b": 0.9}).decision is Decision.ESCALATE


@given(t_d=st.floats(min_value=0.05, max_value=0.95))
@hyp_settings(max_examples=50)
def test_escalation_monotonic_in_t_d(t_d):
    """Lowering t_d can never turn an ESCALATE into a non-ESCALATE."""
    scores = {"a": 0.35, "b": 0.65}  # inside the middle band, so t_d rules
    base = DisagreementGate(Settings(gate_t_d=t_d))
    lower = DisagreementGate(Settings(gate_t_d=max(0.01, t_d - 0.1)))
    if base.decide(scores).decision is Decision.ESCALATE:
        assert lower.decide(scores).decision is Decision.ESCALATE


def test_abs_diff_metric():
    assert disagreement({"a": 0.2, "b": 0.9}, "abs_diff") == pytest.approx(0.7)
    assert disagreement({"a": 0.5}, "abs_diff") == 0.0


def test_region_conflict_metric():
    assert disagreement({"a": 0.2, "b": 0.9}, "region_conflict", t_low=0.3, t_high=0.7) > 0
    assert disagreement({"a": 0.4, "b": 0.6}, "region_conflict", t_low=0.3, t_high=0.7) == 0.0


def test_entropy_metric_peaks_at_half():
    low = disagreement({"a": 0.1, "b": 0.2}, "entropy")
    mid = disagreement({"a": 0.4, "b": 0.6}, "entropy")
    assert mid > low > 0


def test_fusion_baselines():
    scores = {"a": 0.8, "b": 0.1}
    assert mean_fusion(scores) is Decision.PASS  # 0.45 average
    assert max_fusion(scores) is Decision.BLOCK  # 0.8 max
    assert mean_fusion({"a": 0.8, "b": 0.9}) is Decision.BLOCK


def test_effective_score_prefers_escalation_tier():
    gate = DisagreementGate(Settings())
    gd = gate.decide({"a": 0.1, "b": 0.9})
    assert gd.decision is Decision.ESCALATE
    assert effective_score({"a": 0.1, "b": 0.9}, gd, escalation_score=0.95) == 0.95
    assert effective_score({"a": 0.1, "b": 0.9}, gd) == pytest.approx(0.5)


def test_tune_smoke():
    rng = np.random.default_rng(0)
    # synthetic validation set: attacks score high on both channels
    scores, labels = [], []
    for _ in range(60):
        b = rng.random() < 0.5
        labels.append(int(b))
        scores.append({"a": rng.uniform(0.6, 0.95) if b else rng.uniform(0.02, 0.4),
                       "b": rng.uniform(0.6, 0.95) if b else rng.uniform(0.02, 0.4)})
    out = tune(scores, labels, Settings(gate_escalation_rate_target=0.5), n_trials=10)
    assert set(out["best_params"]) == {"t_low", "t_high", "t_d"}
    assert len(out["curve"]) == 10
    assert all(0.0 <= c["escalation_rate"] <= 1.0 for c in out["curve"])
