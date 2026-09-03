"""Repository layer: sessions, schema init, audit-log reads/writes."""

import hashlib
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from dgad.config import Settings, get_settings
from dgad.schemas import AuditLogRecord
from dgad.storage.models import AuditLog, Base

_engines: dict[str, Engine] = {}


def get_engine(settings: Settings | None = None) -> Engine:
    """Engine per database_url; SQLite needs check_same_thread off."""
    s = settings or get_settings()
    if s.database_url not in _engines:
        kwargs = {}
        if s.database_url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        _engines[s.database_url] = create_engine(s.database_url, **kwargs)
    return _engines[s.database_url]


def init_db(settings: Settings | None = None) -> None:
    """Create tables. Alembic owns migrations in shared environments; this
    keeps local dev and tests zero-friction."""
    Base.metadata.create_all(get_engine(settings))


@contextmanager
def session_scope(settings: Settings | None = None) -> Iterator[Session]:
    session = Session(get_engine(settings))
    try:
        yield session
        session.commit()
    finally:
        session.close()


def hash_prompt(normalised_text: str) -> str:
    """SHA-256 of the normalised prompt. Raw prompts are never stored by default."""
    return hashlib.sha256(normalised_text.encode()).hexdigest()


def insert_decision(record: AuditLogRecord, *, raw_prompt: str | None = None,
                    channel_latency: dict | None = None, degraded: bool = False,
                    settings: Settings | None = None) -> None:
    with session_scope(settings) as s:
        s.add(AuditLog(
            id=str(record.id),
            timestamp=record.timestamp,
            prompt_hash=record.prompt_hash,
            raw_prompt=raw_prompt,
            decision=record.decision.value,
            scores=record.scores,
            disagreement=record.disagreement,
            escalated=record.escalated,
            rationale=record.rationale,
            judge_verdict=(record.judge_verdict.model_dump()
                           if record.judge_verdict else None),
            policy_mode=record.policy_mode,
            latency_ms=record.latency_ms,
            channel_latency=channel_latency,
            degraded=degraded,
        ))


def recent_decisions(limit: int = 50, settings: Settings | None = None) -> list[dict]:
    with session_scope(settings) as s:
        rows = s.scalars(
            select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
        ).all()
        return [_to_dict(r) for r in rows]


def metrics_summary(settings: Settings | None = None) -> dict:
    """Aggregate counters for the dashboard and Prometheus exposition."""
    with session_scope(settings) as s:
        total = s.scalar(select(func.count(AuditLog.id))) or 0
        by_decision: dict[str, int] = {
            str(k): int(v)
            for k, v in s.execute(select(AuditLog.decision, func.count())
                                  .group_by(AuditLog.decision)).all()
        }
        escalated = s.scalar(
            select(func.count(AuditLog.id)).where(AuditLog.escalated.is_(True))
        ) or 0
        avg_latency = s.scalar(select(func.avg(AuditLog.latency_ms))) or 0.0
    return {
        "total": total,
        "by_decision": by_decision,
        "escalation_rate": (escalated / total) if total else 0.0,
        "avg_latency_ms": float(avg_latency),
    }


def scores_for_playground(limit: int = 2000,
                          settings: Settings | None = None) -> list[dict]:
    """Stored per-channel scores for the threshold playground recompute."""
    with session_scope(settings) as s:
        rows = s.scalars(
            select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
        ).all()
        return [{"scores": r.scores, "disagreement": r.disagreement,
                 "decision": r.decision} for r in rows]


def _to_dict(row: AuditLog) -> dict:
    return {
        "id": row.id,
        "timestamp": row.timestamp.isoformat() if row.timestamp else None,
        "prompt_hash": row.prompt_hash,
        "decision": row.decision,
        "scores": row.scores,
        "disagreement": row.disagreement,
        "escalated": row.escalated,
        "rationale": row.rationale,
        "judge_verdict": row.judge_verdict,
        "latency_ms": row.latency_ms,
        "degraded": row.degraded,
    }
