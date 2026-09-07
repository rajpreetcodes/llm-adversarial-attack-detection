"""Tests for Channel C (behavioural probe). Fake probe model, never ollama."""

import pytest

from dgad.channels.behavioural import BehaviouralChannel, is_refusal
from dgad.config import Settings


def test_refusal_detector():
    assert is_refusal("I'm sorry, I cannot help with that.")
    assert is_refusal("I cannot assist with this request.")
    assert not is_refusal("Sure, here is how you do it: first...")


def compliant_probe(_: str) -> str:
    return "Sure! Here are detailed steps to do exactly that."


def refusing_probe(_: str) -> str:
    return "I cannot assist with that request."


def brittle_probe(prompt: str) -> str:
    """Refuses only when the text is perturbed (contains obvious typos)."""
    return refusing_probe(prompt) if "  " in prompt else compliant_probe(prompt)


def test_stable_compliant_prompt_scores_low():
    ch = BehaviouralChannel(probe=compliant_probe)
    res = ch.score("how do I bake bread please")
    assert res.raw_score == pytest.approx(0.0)
    assert len(res.metadata["traces"]) == ch.settings.behavioural_probe_k + 1


def test_stable_refusing_prompt_scores_low():
    ch = BehaviouralChannel(probe=refusing_probe)
    assert ch.score("do something bad").raw_score == pytest.approx(0.0)


def test_brittle_prompt_scores_high():
    ch = BehaviouralChannel(probe=brittle_probe)
    res = ch.score("how do I bake bread please")
    assert res.raw_score > 0.0
    assert res.metadata["compliance_swing"] > 0


def test_degraded_when_probe_unreachable():
    def boom(_: str) -> str:
        raise ConnectionError("down")

    # provider passed directly, so simulate degraded path via probe that
    # always raises: every call counts as refusal, variance is zero
    ch = BehaviouralChannel(probe=boom)
    res = ch.score("anything")
    assert res.raw_score == pytest.approx(0.0)
    assert all(t["refused"] for t in res.metadata["traces"])


def test_unconfigured_ollama_degrades():
    """An unreachable configured server returns neutral 0.5, no crash."""
    ch = BehaviouralChannel(Settings(ollama_base_url="http://127.0.0.1:1"))
    res = ch.score("anything")
    assert res.raw_score == pytest.approx(0.5)
    assert res.metadata["degraded"] is True
