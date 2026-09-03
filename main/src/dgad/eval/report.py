"""Report generator (final_plan.md Phase 13 step 6).

Turns the raw result CSVs into every figure in the report. Figures are
GENERATED, never hand-drawn; tables come from ablation.csv, never typed.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import roc_curve  # noqa: E402

from dgad.eval import metrics as ev  # noqa: E402

FIGS = Path("results/figures")


def roc_overlay(results_dir: Path, configs: list[str], out: Path) -> Path:
    """ROC curves of the key configurations overlaid."""
    fig, ax = plt.subplots(figsize=(6, 6))
    for name in configs:
        path = results_dir / f"scores_{name}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        fpr, tpr, _ = roc_curve(df["label"], df["score"])
        auc = float(ev.detection_metrics(df["label"].to_numpy(),
                                         df["score"].to_numpy())["roc_auc"])
        ax.plot(fpr, tpr, label=f"{name} (AUC {auc:.3f})")
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4)
    ax.set_xlabel("false positive rate")
    ax.set_ylabel("true positive rate")
    ax.set_title("ROC: DGAD vs baselines")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def escalation_tradeoff(results_dir: Path, out: Path) -> Path | None:
    """Escalation rate vs AUC: arguably the single most important figure."""
    path = results_dir / "gate_tradeoff_curve.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(df["escalation_rate"], df["roc_auc"], s=12, alpha=0.5)
    ax.set_xlabel("escalation rate (fraction of traffic sent to the judge)")
    ax.set_ylabel("ROC-AUC (validation)")
    ax.set_title("The accuracy/cost trade-off the gate buys")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def per_family_bars(results_dir: Path, configs: list[str], out: Path) -> Path:
    """Per-attack-family detection rate (recall at the tuned threshold).

    Per-family AUC is undefined inside a single split (each family subset is
    single-class), so the report shows the attack detection rate per family:
    the complementarity story in the honest form.
    """
    import numpy as np

    table = pd.read_csv(results_dir / "ablation.csv").set_index("config")
    frames = {}
    for name in configs:
        path = results_dir / f"scores_{name}.csv"
        if path.exists() and name in table.index:
            frames[name] = (pd.read_csv(path), float(table.loc[name, "threshold"]))
    families = sorted({f for fr, _ in frames.values()
                       for f in fr.loc[fr["attack_family"] != "none", "attack_family"]})
    fig, ax = plt.subplots(figsize=(8, 4))
    width = 0.8 / max(1, len(frames))
    x = np.arange(len(families))
    for i, (name, (fr, thr)) in enumerate(frames.items()):
        vals = []
        for f in families:
            sub = fr[(fr["attack_family"] == f) & (fr["label"] == 1)]
            vals.append(float((sub["score"] >= thr).mean()) if len(sub) else float("nan"))
        ax.bar(x + i * width, vals, width, label=name)
    ax.set_xticks(x + width * (len(frames) - 1) / 2)
    ax.set_xticklabels(families, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("attack detection rate (recall)")
    ax.set_ylim(0, 1.05)
    ax.set_title("Per-family detection: complementary blind spots")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def cost_pareto(results_dir: Path, out: Path) -> Path:
    """Cost vs accuracy Pareto frontier across configurations."""
    table = pd.read_csv(results_dir / "ablation.csv")
    table = table.dropna(subset=["roc_auc"])
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(table["cost_per_1000_usd"], table["roc_auc"], s=30)
    for _, r in table.iterrows():
        ax.annotate(r["config"], (r["cost_per_1000_usd"], r["roc_auc"]),
                    fontsize=6, alpha=0.7)
    ax.set_xlabel("estimated cost per 1,000 prompts (USD)")
    ax.set_ylabel("ROC-AUC")
    ax.set_title("Cost/accuracy Pareto frontier")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def generate_all(results_dir: str | Path = "results") -> list[Path]:
    """Regenerate every report figure from raw results. One command."""
    results = Path(results_dir)
    figs = FIGS if results == Path("results") else results / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    key = ["channel_a_only", "channel_b_only", "naive_mean_fusion",
           "dgad_escalate_judge", "dgad_full"]
    made = [
        roc_overlay(results, key, figs / "roc_overlay.png"),
        per_family_bars(results, ["channel_a_only", "channel_b_only", "dgad_full"],
                        figs / "per_family_auc.png"),
        cost_pareto(results, figs / "cost_pareto.png"),
    ]
    trade = escalation_tradeoff(results, figs / "escalation_vs_auc.png")
    if trade:
        made.append(trade)
    return made


if __name__ == "__main__":
    for path in generate_all():
        print(path)
