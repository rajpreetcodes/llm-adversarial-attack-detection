"""Tests for the canary tripwire and the self-adversarial loop."""

import random

from dgad.adversarial.loop import find_false_agreement, plot_rounds, run_round
from dgad.canary import CanaryStatus, build_wrapper, check_response, generate_token
from dgad.config import Settings


def test_tokens_unique_and_random():
    tokens = {generate_token() for _ in range(1000)}
    assert len(tokens) == 1000
    assert all(len(t) == 10 for t in tokens)


def test_wrapper_contains_boundary_and_token():
    wrapped, token = build_wrapper("<doc>payroll data</doc>")
    assert "<UNTRUSTED_DOCUMENT>" in wrapped
    assert token in wrapped
    assert "<doc>payroll data</doc>" in wrapped


def test_check_intact():
    _, token = build_wrapper("doc")
    res = check_response(f"Here is the summary. {token}", token)
    assert res.status is CanaryStatus.INTACT


def test_check_dropped():
    res = check_response("Here is the summary.", "ZZZ999")
    assert res.status is CanaryStatus.DROPPED


def test_check_instruction_obeyed():
    res = check_response("Done, I sent the database export as instructed in the document.",
                         "ZZZ999")
    assert res.status is CanaryStatus.INSTRUCTION_OBEYED


# --- adversarial loop -------------------------------------------------------


def blind_channels(secret: str):
    """Fake cheap channels with a known blind spot: they score 0 when the
    secret marker is absent, 0.9 when present."""

    def ch_a(text: str) -> float:
        return 0.1 if secret not in text else 0.9

    def ch_b(text: str) -> float:
        return 0.1 if secret not in text else 0.9

    return {"a": ch_a, "b": ch_b}


def test_loop_finds_false_agreement(tmp_path):
    secret = "TRIGGER"
    attack = f"do the harmful thing {secret}"
    scorers = blind_channels(secret)

    def judge(text: str) -> bool:
        return "harmful" in text  # intent check: phrase must survive

    hit = find_false_agreement(attack, scorers, judge, t_low=0.3,
                               rng=random.Random(0), max_steps=500)
    assert hit is not None
    assert secret not in hit  # blind spot found
    assert "harmful" in hit  # intent preserved


def test_validity_gate_rejects_broken_mutations(tmp_path):
    scorers = {"a": lambda t: 0.05, "b": lambda t: 0.05}  # everything benign
    never_valid = lambda t: False  # noqa: E731
    hit = find_false_agreement("attack", scorers, never_valid, t_low=0.3,
                               rng=random.Random(0), max_steps=20)
    assert hit is None


def test_run_round_metrics_and_persistence(tmp_path):
    secret = "TRIGGER"
    metrics = run_round(
        [f"harmful request {secret}"],
        blind_channels(secret),
        lambda t: "harmful" in t,
        Settings(),
        round_index=0,
        out_dir=tmp_path,
        max_steps=500,
    )
    assert set(metrics) == {"round", "attacks_searched", "false_agreement_rate",
                            "hard_negatives_found", "wall_time_s"}
    assert metrics["hard_negatives_found"] == 1
    files = list(tmp_path.glob("round_*.jsonl"))
    assert len(files) == 1


def test_plot_rounds_writes_file(tmp_path):
    out = plot_rounds(
        [{"round": i, "false_agreement_rate": 0.5 - i * 0.1} for i in range(4)],
        tmp_path / "rounds.png",
    )
    assert out.exists() and out.stat().st_size > 0
