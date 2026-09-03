"""SQLAlchemy models for the audit log (final_plan.md Phase 11 step 4).

Privacy by default: we store the SHA-256 hash of the normalised prompt, not
the raw text. Raw storage is an explicit opt-in setting and off by default.
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AuditLog(Base):
    """One row per detection decision."""

    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=lambda: str(uuid4()))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                default=lambda: datetime.now(UTC))
    prompt_hash: Mapped[str] = mapped_column(String(64), index=True)
    raw_prompt: Mapped[str | None] = mapped_column(Text, nullable=True,
                                                   default=None)  # opt-in only
    decision: Mapped[str] = mapped_column(String(16), index=True)
    scores: Mapped[dict] = mapped_column(JSON)
    disagreement: Mapped[float] = mapped_column(Float)
    escalated: Mapped[bool] = mapped_column(Boolean)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    judge_verdict: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    policy_mode: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[float] = mapped_column(Float)
    channel_latency: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    degraded: Mapped[bool] = mapped_column(Boolean, default=False)
