"""Tests for Channel B (semantic) with a fake embedder. No model downloads."""

import numpy as np
import pytest
from sklearn.metrics import roc_auc_score

from dgad.channels.semantic import SemanticChannel, hashing_embedder


def two_cluster_embedder(dim: int = 8):
    """Fake embedder: attacks cluster near +1, benign near -1 on axis 0."""

    def encode(texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), dim))
        for i, t in enumerate(texts):
            out[i, 0] = 1.0 if "ATTACK" in t else -1.0
            out[i, 1] = len(t) % 5 / 5.0  # noise axis
        return out

    return encode


def test_trained_head_separates_clusters():
    texts = [("ATTACK do bad thing " * (i % 3 + 1)) for i in range(20)]
    texts += [("what is the weather " * (i % 3 + 1)) for i in range(20)]
    labels = [1] * 20 + [0] * 20
    ch = SemanticChannel(embedder=two_cluster_embedder()).fit(texts, labels)
    scores = np.array([ch.score(t).raw_score for t in texts])
    assert roc_auc_score(labels, scores) == pytest.approx(1.0)


def test_score_contract():
    ch = SemanticChannel(embedder=two_cluster_embedder())
    ch.fit(["ATTACK x", "hello y"], [1, 0])
    res = ch.score("ATTACK now")
    assert 0.0 <= res.raw_score <= 1.0
    assert res.latency_ms >= 0
    assert res.calibrated_score is None  # calibration layer fills this


def test_untrained_raises_clear_error():
    ch = SemanticChannel(embedder=two_cluster_embedder())
    with pytest.raises(RuntimeError, match="not trained"):
        ch.score("anything")


def test_save_load(tmp_path):
    ch = SemanticChannel(embedder=two_cluster_embedder())
    ch.fit(["ATTACK x", "hello y"], [1, 0])
    ch.save(tmp_path)
    ch2 = SemanticChannel(embedder=two_cluster_embedder()).load(tmp_path)
    assert ch2.score("ATTACK z").raw_score == pytest.approx(ch.score("ATTACK z").raw_score)


def test_hashing_embedder_deterministic_and_normalised():
    emb = hashing_embedder(dim=32)
    a = emb(["the quick brown fox"])
    b = emb(["the quick brown fox"])
    np.testing.assert_allclose(a, b)
    assert np.linalg.norm(a[0]) == pytest.approx(1.0)
