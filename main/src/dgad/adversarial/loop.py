"""Self-adversarial calibration loop (final_plan.md Phase 10, SECOND NOVELTY).

The gate has one structural weakness: an attack that looks innocent to EVERY
cheap channel at once produces agreement, nothing escalates, and it sails
through. This loop is a small attacker whose only goal is to find prompts in
that hole ("false agreement"), verified by a judge so we do not collect
mutations that merely broke the attack. Everything it finds becomes a
versioned hard-negative dataset used to retrain Channel B, re-fit
calibrators, and re-tune the gate.

Formal objective: starting from known attack x, find mutation x' such that
max_i s_i(x') <= t_low for all cheap channels i (agreement on benign) while
judge(x') still says attack. Hill-climbing over the mutation operators is
the baseline search; escalate to a genetic algorithm only if it stalls.

Known failure mode (guarded, reported): the loop can overfit to its own
mutators. Hold out attack families the loop never touches and confirm their
detection does not degrade.
"""

import json
import random
import time
from collections.abc import Callable, Mapping
from pathlib import Path

from dgad.adversarial.mutators import random_mutation
from dgad.config import Settings, get_settings

ChannelScorer = Callable[[str], float]
JudgeFn = Callable[[str], bool]  # True = attack intent preserved


def find_false_agreement(
    attack: str,
    cheap_scorers: Mapping[str, ChannelScorer],
    judge: JudgeFn,
    t_low: float,
    rng: random.Random,
    max_steps: int = 200,
) -> str | None:
    """Hill-climb mutations of `attack` toward cross-channel false agreement.

    A candidate is accepted only when every cheap channel scores it at or
    below t_low AND the judge confirms the attack intent survived. Returns
    the winning mutation or None within the step budget.
    """
    candidate = attack
    for _ in range(max_steps):
        mutated = random_mutation(rng, candidate, strength=rng.choice([1, 1, 2]))
        scores = {name: scorer(mutated) for name, scorer in cheap_scorers.items()}
        if all(s <= t_low for s in scores.values()) and judge(mutated):
            return mutated
        # hill-climb: keep whichever variant the channels find least suspicious
        current_max = max(scorer(candidate) for scorer in cheap_scorers.values())
        if max(scores.values()) < current_max:
            candidate = mutated
    return None


def run_round(
    attacks: list[str],
    cheap_scorers: Mapping[str, ChannelScorer],
    judge: JudgeFn,
    settings: Settings | None = None,
    round_index: int = 0,
    out_dir: str | Path | None = None,
    max_steps: int = 200,
) -> dict:
    """One loop round: hunt false agreements, persist hard negatives.

    Returns the per-round metrics dict logged to the experiment tracker.
    """
    s = settings or get_settings()
    rng = random.Random(s.random_seed + round_index)
    found: list[dict] = []
    start = time.perf_counter()
    for attack in attacks:
        hit = find_false_agreement(
            attack, cheap_scorers, judge, s.gate_t_low, rng, max_steps=max_steps
        )
        if hit is not None:
            found.append({"original": attack, "mutated": hit, "round": round_index})
    if found:
        root = Path(out_dir or Path(s.data_dir) / "processed" / "hard_negatives")
        root.mkdir(parents=True, exist_ok=True)
        with (root / f"round_{round_index:03d}.jsonl").open("a", encoding="utf-8") as fh:
            for rec in found:
                fh.write(json.dumps(rec) + "\n")
    return {
        "round": round_index,
        "attacks_searched": len(attacks),
        "false_agreement_rate": (len(found) / len(attacks)) if attacks else 0.0,
        "hard_negatives_found": len(found),
        "wall_time_s": time.perf_counter() - start,
    }


def plot_rounds(round_metrics: list[dict], out_path: str | Path) -> Path:
    """Round-over-round hardening plot: false-agreement rate should fall.

    This is the second headline figure of the report.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rounds = [m["round"] for m in round_metrics]
    rates = [m["false_agreement_rate"] for m in round_metrics]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(rounds, rates, "o-")
    ax.set_xlabel("adversarial loop round")
    ax.set_ylabel("false-agreement rate")
    ax.set_title("Self-adversarial hardening")
    ax.set_ylim(0, 1)
    fig.tight_layout()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out
