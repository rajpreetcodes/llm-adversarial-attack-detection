"""Tests for the calibration layer."""

import numpy as np
import pytest

from dgad.calibration import Calibrator, expected_calibration_error, reliability_diagram


def skewed_data(n: int = 400, seed: int = 0):
    """Scores that rank well but are systematically overconfident."""
    rng = np.random.default_rng(seed)
    labels = (rng.random(n) < 0.5).astype(int)
    raw = np.where(labels == 1, rng.beta(5, 2, n), rng.beta(2, 5, n))
    overconfident = np.clip(raw ** 3, 0, 1)  # squash toward 0: badly calibrated
    return overconfident, labels


@pytest.mark.parametrize("method", ["platt", "isotonic"])
def test_calibration_reduces_ece(method):
    raw, labels = skewed_data()
    cal = Calibrator("test", method).fit(raw, labels)
    after = cal.transform(raw)
    assert expected_calibration_error(after, labels) < expected_calibration_error(raw, labels)


@pytest.mark.parametrize("method", ["platt", "isotonic"])
def test_transform_monotonic_in_unit_interval(method):
    raw, labels = skewed_data()
    cal = Calibrator("test", method).fit(raw, labels)
    grid = np.linspace(raw.min(), raw.max(), 50)
    out = cal.transform(grid)
    assert out.min() >= 0.0 and out.max() <= 1.0
    assert np.all(np.diff(out) >= -1e-8)


def test_save_load_roundtrip(tmp_path):
    raw, labels = skewed_data()
    cal = Calibrator("chan", "platt").fit(raw, labels)
    path = cal.save(tmp_path)
    loaded = Calibrator.load(path)
    np.testing.assert_allclose(loaded.transform(raw), cal.transform(raw))


def test_unfitted_transform_raises():
    with pytest.raises(RuntimeError):
        Calibrator("chan", "platt").transform(np.array([0.5]))


def test_ece_bounds():
    labels = np.array([0, 0, 1, 1])
    perfect = np.array([0.0, 0.0, 1.0, 1.0])
    assert expected_calibration_error(perfect, labels) == pytest.approx(0.0)


def test_reliability_diagram_writes_file(tmp_path):
    raw, labels = skewed_data(100)
    cal = Calibrator("chan", "platt").fit(raw, labels)
    out = reliability_diagram(raw, cal.transform(raw), labels, "t", tmp_path / "rel.png")
    assert out.exists() and out.stat().st_size > 0
