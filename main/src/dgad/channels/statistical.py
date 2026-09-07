"""Channel A: statistical detection (final_plan.md Phase 2).

Windowed perplexity (Jain et al., Baseline Defenses): a clever attacker hides
a short weird suffix inside a long normal paragraph, so whole-prompt
perplexity looks fine; sliding a window and taking the WORST window exposes
it. Token-anomaly features catch obfuscation that perplexity misses.

GPT-2 is loaded lazily, once, and cached in memory. When the model is not
available (offline CI, tests) the channel scores from the anomaly features
alone and marks metadata.degraded.
"""

import math
import time
from pathlib import Path

import joblib
import numpy as np

from dgad.channels.base import Channel
from dgad.config import Settings, get_settings
from dgad.schemas import ChannelResult

_ZERO_WIDTH = ["​", "‌", "‍", "⁠", "﻿"]

_MODEL_CACHE: dict[str, tuple] = {}


def _load_gpt2(model_name: str) -> tuple:
    """Lazy singleton load of the perplexity reference model."""
    if model_name not in _MODEL_CACHE:
        from transformers import AutoTokenizer, GPT2LMHeadModel

        tok = AutoTokenizer.from_pretrained(model_name)
        model = GPT2LMHeadModel.from_pretrained(model_name)
        model.eval()
        _MODEL_CACHE[model_name] = (tok, model)
    return _MODEL_CACHE[model_name]


def _sliding_windows(ids: list[int], window: int, stride: int) -> list[list[int]]:
    """Return fixed windows plus a final tail-aligned window."""
    if window <= 0 or stride <= 0:
        raise ValueError("window and stride must be positive")
    if len(ids) <= window:
        return [ids]
    starts = list(range(0, len(ids) - window + 1, stride))
    tail_start = len(ids) - window
    if starts[-1] != tail_start:
        starts.append(tail_start)
    return [ids[i:i + window] for i in starts]


def windowed_perplexity(text: str, model_name: str, window: int, stride: int) -> float:
    """Max perplexity over sliding windows of `window` tokens at `stride`."""
    import torch

    tok, model = _load_gpt2(model_name)
    ids = tok.encode(text)
    if len(ids) < 2:
        return 1.0
    windows = _sliding_windows(ids, window, stride)
    worst = 0.0
    for w in windows:
        if len(w) < 2:
            continue
        t = torch.tensor([w])
        with torch.no_grad():
            nll = model(t, labels=t).loss.item()
        worst = max(worst, math.exp(min(nll, 20.0)))
    return worst


def anomaly_features(text: str) -> np.ndarray:
    """Surface features that catch obfuscation and adversarial suffixes.

    Returns a fixed-length vector:
    [non_ascii_ratio, punct_ratio, zero_width_count, longest_run,
     single_char_token_ratio, char_entropy]
    """
    if not text:
        return np.zeros(6)
    n = len(text)
    non_ascii = sum(1 for c in text if ord(c) > 127) / n
    punct = sum(1 for c in text if not c.isalnum() and not c.isspace()) / n
    zw = sum(text.count(c) for c in _ZERO_WIDTH)
    longest_run = max((len(run) for run in text.split()), default=0) / n
    tokens = text.split()
    single_char = (sum(1 for t in tokens if len(t) == 1) / len(tokens)) if tokens else 0.0
    counts = np.bincount(np.frombuffer(text.encode("utf-8", "ignore"), dtype=np.uint8))
    probs = counts[counts > 0] / counts.sum()
    entropy = float(-(probs * np.log2(probs)).sum()) / 8.0  # normalise to [0, 1]
    return np.array([non_ascii, punct, float(zw), longest_run, single_char, entropy],
                    dtype=float)


def _squash(log_ppl: float) -> float:
    """Map log-perplexity to [0, 1]; GPT-2 English prose sits near log 2-4."""
    return float(1.0 / (1.0 + math.exp(-(log_ppl - 6.0))))


class StatisticalChannel(Channel):
    """Windowed perplexity + token-anomaly scorer.

    If a fitted logistic-regression combiner exists (see fit()), it is used;
    otherwise a documented heuristic blends squashed max-window perplexity
    with the anomaly features. Set use_model=False to skip GPT-2 entirely
    (feature-only mode, used by tests and the offline synthetic eval).
    """

    name = "statistical"

    def __init__(self, settings: Settings | None = None, *, use_model: bool = True) -> None:
        self.settings = settings or get_settings()
        self.use_model = use_model
        self._combiner = None

    def fit(self, texts: list[str], labels: list[int]) -> "StatisticalChannel":
        """Fit the LR combiner on [log max-window ppl, anomaly features]."""
        from sklearn.linear_model import LogisticRegression

        x = np.array([self._feature_row(t) for t in texts])
        self._combiner = LogisticRegression(max_iter=1000).fit(x, np.asarray(labels))
        return self

    def _feature_row(self, text: str) -> np.ndarray:
        feats = anomaly_features(text)
        if self.use_model:
            try:
                ppl = windowed_perplexity(
                    text,
                    self.settings.perplexity_model,
                    self.settings.perplexity_window,
                    self.settings.perplexity_stride,
                )
                return np.concatenate([[math.log(max(ppl, 1e-6))], feats])
            except Exception:
                pass  # fall through to feature-only
        return np.concatenate([[0.0], feats])

    def save(self, directory: str | Path) -> Path:
        path = Path(directory) / "channel_a_combiner.joblib"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._combiner, path)
        # marker records which scoring mode the combiner was fitted in, so a
        # serving process never mixes feature-only weights with GPT-2 scores
        (path.parent / "channel_a_mode.txt").write_text(
            "model" if self.use_model else "features")
        return path

    def load(self, directory: str | Path) -> "StatisticalChannel":
        path = Path(directory) / "channel_a_combiner.joblib"
        self._combiner = joblib.load(path) if path.exists() else None
        marker = Path(directory) / "channel_a_mode.txt"
        if marker.exists():
            self.use_model = marker.read_text().strip() == "model"
        return self

    def score(self, text: str) -> ChannelResult:
        start = time.perf_counter()
        row = self._feature_row(text)
        degraded = bool(self.use_model and row[0] == 0.0)
        if self._combiner is not None:
            raw = float(self._combiner.predict_proba(row.reshape(1, -1))[0, 1])
        else:
            # ponytail: heuristic blend until fit() has run; ppl term is 0 in
            # feature-only mode so weights stay meaningful in both modes.
            log_ppl = row[0]
            feats = row[1:]
            anomaly = float(np.clip(feats[0] + feats[1] + min(feats[2], 5) / 5
                                    + feats[3] + feats[4], 0, 3) / 3)
            raw = 0.7 * _squash(log_ppl) + 0.3 * anomaly if not degraded else anomaly
        latency = (time.perf_counter() - start) * 1000
        return ChannelResult(
            raw_score=float(np.clip(raw, 0.0, 1.0)),
            latency_ms=latency,
            metadata={
                "degraded": degraded,
                "log_max_window_ppl": float(row[0]),
                "anomaly_features": row[1:].tolist(),
            },
        )
