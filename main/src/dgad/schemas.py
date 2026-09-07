"""Cross-module payload contracts.

These pydantic models are the interface every build agent codes against.
Keep them stable and minimal: additive changes are fine, renames or type
changes break other modules.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Decision(StrEnum):
    """The three possible outputs of the disagreement gate."""

    PASS = "PASS"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


class ChannelResult(BaseModel):
    """Output of a single detection channel.

    Contract (final_plan.md, Phase 0 step 6): every channel returns exactly
    this shape so channels can be swapped in and out for the ablation study
    without rewriting anything else.
    """

    raw_score: float = Field(
        description="Uncalibrated channel score, higher means more attack-like"
    )
    calibrated_score: float | None = Field(
        default=None,
        description="Score after the calibration layer; None until calibration has run",
    )
    latency_ms: float = Field(description="Wall-clock time the channel spent scoring, in ms")
    metadata: dict = Field(default_factory=dict, description="Channel-specific debug details")


class GateDecision(BaseModel):
    """Output of the disagreement gate for one prompt."""

    decision: Decision
    scores: dict[str, float] = Field(
        description="Calibrated score per channel name, e.g. {'statistical': 0.12}"
    )
    disagreement: float = Field(description="Value of the configured disagreement metric")
    rationale: str | None = Field(
        default=None,
        description="Human-readable explanation, populated on escalation or by the judge",
    )


class JudgeVerdict(BaseModel):
    """Output of Channel D, the LLM-as-a-judge."""

    verdict: Literal["attack", "benign"]
    confidence: float = Field(ge=0.0, le=1.0)
    attack_family: str | None = Field(
        default=None,
        description=(
            "e.g. gcg_optimised, jailbreak_roleplay, injection_direct, "
            "injection_indirect, obfuscation"
        ),
    )
    rationale: str = Field(description="Natural-language explanation from the judge")


class DetectRequest(BaseModel):
    """Request body for POST /v1/detect."""

    prompt: str = Field(min_length=1)


class DetectResponse(BaseModel):
    """Response body for POST /v1/detect."""

    decision: Decision
    scores: dict[str, float]
    disagreement: float
    rationale: str | None = None
    escalated: bool = Field(description="True if the prompt was sent to the escalation tier")
    latency_ms: float
    channel_results: dict[str, ChannelResult] = Field(
        default_factory=dict,
        description="Raw and calibrated result, health, and metadata for each channel",
    )
    degraded: bool = Field(
        default=False,
        description="True when any required or escalation channel degraded",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Detection-path metadata for clients and the prompt-inspection UI",
    )


class AuditLogRecord(BaseModel):
    """One row of the audit log, written to the database for every decision."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    prompt_hash: str = Field(
        description="SHA-256 of the normalised prompt; raw prompts are never stored"
    )
    decision: Decision
    scores: dict[str, float]
    disagreement: float
    escalated: bool
    rationale: str | None = None
    judge_verdict: JudgeVerdict | None = None
    policy_mode: str
    latency_ms: float
