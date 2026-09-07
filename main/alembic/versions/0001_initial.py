"""0001: initial audit_log table.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-13
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("raw_prompt", sa.Text, nullable=True),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("scores", sa.JSON, nullable=False),
        sa.Column("disagreement", sa.Float, nullable=False),
        sa.Column("escalated", sa.Boolean, nullable=False),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("judge_verdict", sa.JSON, nullable=True),
        sa.Column("policy_mode", sa.String(32), nullable=False),
        sa.Column("latency_ms", sa.Float, nullable=False),
        sa.Column("channel_latency", sa.JSON, nullable=True),
        sa.Column("degraded", sa.Boolean, nullable=False),
    )
    op.create_index("ix_audit_log_prompt_hash", "audit_log", ["prompt_hash"])
    op.create_index("ix_audit_log_decision", "audit_log", ["decision"])


def downgrade() -> None:
    op.drop_table("audit_log")
