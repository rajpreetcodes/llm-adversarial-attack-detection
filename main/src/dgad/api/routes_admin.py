"""Admin routes: recent decisions, metrics summary, threshold playground."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from dgad.config import Settings
from dgad.gate import DisagreementGate
from dgad.storage import repo

router = APIRouter(prefix="/admin")


@router.get("/logs", include_in_schema=False)
@router.get("/decisions")
def decisions(limit: int = 50) -> list[dict]:
    """Recent decisions for the dashboard live feed."""
    return repo.recent_decisions(limit=min(limit, 500))


@router.get("/stats", include_in_schema=False)
@router.get("/metrics-summary")
def metrics_summary() -> dict:
    """Aggregate counters: totals, decision mix, escalation rate, latency."""
    return repo.metrics_summary()


class PlaygroundRequest(BaseModel):
    """Threshold playground: recompute decisions over historical scores."""

    t_low: float = Field(ge=0.0, le=1.0)
    t_high: float = Field(ge=0.0, le=1.0)
    t_d: float = Field(ge=0.0, le=1.0)


@router.post("/playground")
def playground(req: PlaygroundRequest) -> dict:
    """Recompute the gate over stored scores with hypothetical thresholds.

    Powers the viva demo: move the sliders, watch the escalation rate and
    decision mix change over real historical traffic.
    """
    rows = repo.scores_for_playground()
    gate = DisagreementGate(Settings(gate_t_low=req.t_low, gate_t_high=req.t_high,
                                     gate_t_d=req.t_d))
    counts = {"PASS": 0, "BLOCK": 0, "ESCALATE": 0}
    for row in rows:
        if row["scores"]:
            counts[gate.decide(row["scores"]).decision.value] += 1
    total = max(1, sum(counts.values()))
    return {"n": len(rows), "decision_mix": counts,
            "escalation_rate": counts["ESCALATE"] / total,
            "thresholds": req.model_dump()}
