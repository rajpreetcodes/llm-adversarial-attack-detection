"""Score calibration layer (final_plan.md Phase 4).

Raw channel scores live on different scales (a perplexity of 340 versus a
probability of 0.71). Calibration maps each channel's raw score to an honest
probability in [0, 1], which is what makes the disagreement gate meaningful:
calibration MUST run before the gate.

Calibrators are fitted on the validation split only, never on train (the
model is overconfident there) and never on test or holdout.
"""

from pathlib import Path

import joblib
import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from dgad.config import Settings, get_settings


def expected_calibration_error(scores: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error: mean gap between confidence and accuracy."""
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels, dtype=float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        mask = (scores > lo) & (scores <= hi)
        if mask.any():
            ece += mask.mean() * abs(scores[mask].mean() - labels[mask].mean())
    return float(ece)


class Calibrator:
    """Per-channel score calibrator: Platt (sigmoid) or isotonic.

    Platt suits small validation sets and assumes a sigmoid distortion;
    isotonic is flexible but needs more data. The choice lives in config and
    the empirical comparison is part of the evaluation report.
    """

    def __init__(self, channel_name: str, method: str | None = None,
                 settings: Settings | None = None) -> None:
        self.channel_name = channel_name
        self.method = method or (settings or get_settings()).calibration_method
        self._platt: LogisticRegression | None = None
        self._iso: IsotonicRegression | None = None

    def fit(self, scores: np.ndarray, labels: np.ndarray) -> "Calibrator":
        """Fit on validation-split raw scores and binary labels."""
        x = np.asarray(scores, dtype=float)
        y = np.asarray(labels, dtype=int)
        if self.method == "platt":
            self._platt = LogisticRegression()
            self._platt.fit(x.reshape(-1, 1), y)
        elif self.method == "isotonic":
            self._iso = IsotonicRegression(out_of_bounds="clip")
            self._iso.fit(x, y)
        else:
            raise ValueError(f"unknown calibration method: {self.method}")
        return self

    def transform(self, scores: np.ndarray) -> np.ndarray:
        """Map raw scores to calibrated probabilities in [0, 1]."""
        x = np.asarray(scores, dtype=float)
        if self._platt is not None:
            return self._platt.predict_proba(x.reshape(-1, 1))[:, 1]
        if self._iso is not None:
            return np.asarray(self._iso.predict(x), dtype=float)
        raise RuntimeError(f"calibrator for {self.channel_name} is not fitted")

    def save(self, directory: str | Path) -> Path:
        """Persist alongside the channel it calibrates (versioned by name)."""
        path = Path(directory) / f"calibrator_{self.channel_name}_{self.method}.joblib"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    @staticmethod
    def load(path: str | Path) -> "Calibrator":
        """Load a persisted calibrator."""
        obj = joblib.load(path)
        if not isinstance(obj, Calibrator):
            raise TypeError(f"{path} does not contain a Calibrator")
        return obj


def reliability_diagram(scores_before: np.ndarray, scores_after: np.ndarray,
                        labels: np.ndarray, title: str, out_path: str | Path,
                        n_bins: int = 10) -> Path:
    """Plot reliability curves before and after calibration (report figure)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def curve(scores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        edges = np.linspace(0.0, 1.0, n_bins + 1)
        centres, accs = [], []
        for lo, hi in zip(edges[:-1], edges[1:], strict=True):
            mask = (scores > lo) & (scores <= hi)
            if mask.any():
                centres.append(float(scores[mask].mean()))
                accs.append(float(labels[mask].mean()))
        return np.array(centres), np.array(accs)

    labels = np.asarray(labels, dtype=float)
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], "k--", label="perfect calibration")
    for scores, name in ((scores_before, "before"), (scores_after, "after")):
        x, y = curve(np.asarray(scores, dtype=float))
        ax.plot(x, y, "o-", label=name)
    ax.set_xlabel("mean predicted probability")
    ax.set_ylabel("observed frequency")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out
