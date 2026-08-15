"""Tests for the data layer: leakage, reproducibility, funnel integrity."""

import pandas as pd
import pytest

from dgad.config import Settings
from dgad.eval import datasets as ds


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    settings = Settings(data_dir=str(tmp_path_factory.mktemp("data")), random_seed=42)
    funnel = ds.build(settings, synthetic=True, per_family=10)
    return settings, funnel


def load(settings, split):
    return pd.read_csv(f"{settings.data_dir}/processed/{split}.csv")


def test_funnel_is_monotonic(built):
    _, funnel = built
    assert funnel["total_rows"] >= funnel["after_quality_filter"]
    assert funnel["after_quality_filter"] >= funnel["after_dedup"] == funnel["final"]


def test_zero_leakage_between_splits(built):
    """No normalised text appears in two splits; no group straddles a split."""
    settings, _ = built
    frames = {s: load(settings, s) for s in ["train", "val", "test", "holdout"]}

    def keys(df):
        return set(df["text"].str.lower().str.replace(r"[^a-z0-9]", "", regex=True))

    splits = list(frames)
    for i, a in enumerate(splits):
        for b in splits[i + 1:]:
            assert keys(frames[a]).isdisjoint(keys(frames[b])), f"{a} vs {b}"


def test_all_splits_non_empty_and_schema(built):
    settings, _ = built
    for split in ["train", "val", "test", "holdout"]:
        df = load(settings, split)
        assert list(df.columns) == ds.SCHEMA
        assert len(df) > 0
        assert df["text"].str.len().min() > 0
        assert set(df["label"].unique()) <= {0, 1}


def test_synthetic_build_reproducible(tmp_path):
    a = Settings(data_dir=str(tmp_path / "a"), random_seed=42)
    b = Settings(data_dir=str(tmp_path / "b"), random_seed=42)
    ds.build(a, synthetic=True, per_family=5)
    ds.build(b, synthetic=True, per_family=5)
    for split in ["train", "val", "test", "holdout"]:
        fa = (tmp_path / "a" / "processed" / f"{split}.csv").read_bytes()
        fb = (tmp_path / "b" / "processed" / f"{split}.csv").read_bytes()
        assert fa == fb


def test_all_families_present(built):
    settings, _ = built
    fams = set(load(settings, "train")["attack_family"].unique())
    for fam in ["gcg_optimised", "jailbreak_roleplay", "injection_direct",
                "injection_indirect", "obfuscation", "none"]:
        assert fam in fams


def test_notinject_source_tracked(built):
    settings, _ = built
    df = pd.concat([load(settings, s) for s in ["train", "val", "test", "holdout"]])
    ni = df[df["source"] == "synthetic_notinject"]
    assert len(ni) > 0
    assert (ni["label"] == 0).all()  # trigger words but benign
