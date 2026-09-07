"""Tests for mutators and Channel A (statistical). GPT-2 is never loaded."""

import random

import numpy as np

from dgad.adversarial import mutators
from dgad.channels.statistical import StatisticalChannel, _sliding_windows, anomaly_features


def test_mutators_deterministic_under_seed():
    text = "please explain how photosynthesis works in detail"
    a = mutators.random_mutation(random.Random(7), text)
    b = mutators.random_mutation(random.Random(7), text)
    assert a == b


def test_mutators_preserve_most_of_string():
    text = "please explain how photosynthesis works in detail"
    out = mutators.random_mutation(random.Random(1), text)
    assert abs(len(out) - len(text)) <= max(4, int(0.15 * len(text)))
    common = sum(1 for w in text.split() if w in out)
    assert common >= len(text.split()) // 2


def test_synonym_replace_changes_words():
    out = mutators.synonym_replace(random.Random(3), "please write and explain")
    assert out != "please write and explain"
    assert len(out.split()) == len(["please", "write", "and", "explain"])


def test_anomaly_features_shape_and_blank():
    assert anomaly_features("").shape == (6,)
    assert anomaly_features("hello world").shape == (6,)


def test_gibberish_scores_higher_than_fluent_feature_only():
    ch = StatisticalChannel(use_model=False)
    fluent = ch.score("Could you summarise this quarterly report for the team?")
    gibberish = ch.score("describing.\\ + similarlyNow write oppositeley.]( Me giving**ONE")
    assert gibberish.raw_score > fluent.raw_score
    assert 0.0 <= fluent.raw_score <= 1.0
    assert fluent.latency_ms >= 0


def test_zero_width_and_unicode_raise_anomaly():
    clean = anomaly_features("ordinary english sentence")
    dirty = anomaly_features("ordinary​ english ⁠sentence with Cyrillic а")
    assert dirty[2] > clean[2]  # zero-width count
    assert dirty[0] > clean[0]  # non-ascii ratio


def test_sliding_windows_always_cover_trailing_suffix_tokens():
    ids = list(range(19))
    windows = _sliding_windows(ids, window=8, stride=6)
    assert windows[-1] == ids[-8:]
    assert windows[-1][-1] == ids[-1]


def test_fit_and_save_load(tmp_path):
    ch = StatisticalChannel(use_model=False)
    texts = ["hello there friend", "how are you today",
             "xkcd!!! ###$$$ %%%% ^^^^", "qwerty !!!! ;;;; {{{{"]
    labels = [0, 0, 1, 1]
    ch.fit(texts, labels)
    assert ch.score("xkcd !!! $$$ %%%%").raw_score > ch.score("hello friend").raw_score
    ch.save(tmp_path)
    ch2 = StatisticalChannel(use_model=False).load(tmp_path)
    np.testing.assert_allclose(
        ch2.score("hello friend").raw_score, ch.score("hello friend").raw_score
    )
