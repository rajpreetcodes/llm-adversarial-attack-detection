"""The detection pipeline: one request's journey, end to end.

normalise -> cheap channels (A, B, E) -> calibration -> disagreement gate
-> (contested only) escalation to judge + behavioural probe -> decision
-> audit log.

Every channel degrades independently: a missing model or an unreachable
service never turns into a 500; it becomes a degraded flag in the metadata.
With zero healthy channels the pipeline fails closed (ESCALATE) rather than
waving traffic through blind.
"""

import hashlib
import time
from pathlib import Path

import numpy as np

from dgad.calibration import Calibrator
from dgad.channels.base import Channel
from dgad.config import Settings, get_settings
from dgad.gate import DisagreementGate
from dgad.normalise import normalise
from dgad.schemas import (
    AuditLogRecord,
    ChannelResult,
    Decision,
    DetectResponse,
    JudgeVerdict,
)


def default_channels(settings: Settings) -> dict[str, Channel]:
    """Cheap channels A, B, E with production defaults (lazy model loads)."""
    from dgad.channels.offset import OffsetChannel
    from dgad.channels.semantic import SemanticChannel
    from dgad.channels.statistical import StatisticalChannel

    ch_a = StatisticalChannel(settings)
    if (Path(settings.models_dir) / "channel_a_combiner.joblib").exists():
        ch_a.load(settings.models_dir)
    ch_b = SemanticChannel(settings)
    head = Path(settings.models_dir) / "channel_b_head.joblib"
    if head.exists():
        ch_b.load(settings.models_dir)
    return {
        "statistical": ch_a,
        "semantic": ch_b,
        "offset": OffsetChannel(settings),
    }


def load_calibrators(settings: Settings) -> dict[str, Calibrator]:
    """Load any persisted calibrators from models_dir (empty dict if none)."""
    root = Path(settings.models_dir)
    out: dict[str, Calibrator] = {}
    if root.exists():
        for path in root.glob("calibrator_*.joblib"):
            cal = Calibrator.load(path)
            out[cal.channel_name] = cal
    return out


class DetectionPipeline:
    """Dependency-injected orchestrator; tests swap in fake channels."""

    def __init__(self, settings: Settings | None = None,
                 channels: dict[str, Channel] | None = None,
                 calibrators: dict[str, Calibrator] | None = None,
                 judge: Channel | None = None,
                 probe: Channel | None = None) -> None:
        self.settings = settings or get_settings()
        self.channels = channels if channels is not None else default_channels(self.settings)
        self.calibrators = (calibrators if calibrators is not None
                            else load_calibrators(self.settings))
        self.gate = DisagreementGate(self.settings)
        self._judge = judge
        self._probe = probe

    def _score_channel(self, name: str, ch: Channel, text: str) -> ChannelResult:
        try:
            return ch.score(text)
        except Exception as exc:
            return ChannelResult(raw_score=0.5, latency_ms=0.0,
                                 metadata={"degraded": True, "error": str(exc)[:200]})

    def _get_judge(self) -> Channel:
        if self._judge is None:
            from dgad.channels.judge import JudgeChannel

            self._judge = JudgeChannel(self.settings)
        return self._judge

    def _get_probe(self) -> Channel:
        if self._probe is None:
            from dgad.channels.behavioural import BehaviouralChannel

            self._probe = BehaviouralChannel(self.settings)
        return self._probe

    def detect(self, prompt: str) -> tuple[DetectResponse, AuditLogRecord, dict]:
        """Run the full pipeline on one raw prompt."""
        start = time.perf_counter()
        text = normalise(prompt)
        results: dict[str, ChannelResult] = {}
        degraded_any = False
        for name, ch in self.channels.items():
            res = self._score_channel(name, ch, text)
            degraded_any = degraded_any or bool(res.metadata.get("degraded"))
            cal = self.calibrators.get(name)
            if cal is not None:
                res.calibrated_score = float(cal.transform(np.array([res.raw_score]))[0])
            results[name] = res
        scores = {n: (r.calibrated_score if r.calibrated_score is not None
                      else r.raw_score)
                  for n, r in results.items()}
        healthy_scores = {n: v for n, v in scores.items()
                          if not results[n].metadata.get("degraded")}
        if not healthy_scores:
            # zero healthy channels: fail closed into the escalation tier
            gd = self.gate.decide({"_unhealthy": 0.5})
            gd.decision = Decision.ESCALATE
        else:
            gd = self.gate.decide(healthy_scores)
        gd.scores = scores
        escalated = gd.decision is Decision.ESCALATE
        verdict: JudgeVerdict | None = None
        final = gd.decision
        if escalated:
            jres = self._score_channel("judge", self._get_judge(), text)
            verdict = (JudgeVerdict(**jres.metadata["verdict"])
                       if "verdict" in jres.metadata else None)
            pres = self._score_channel("behavioural", self._get_probe(), text)
            judge_score = jres.raw_score
            if not pres.metadata.get("degraded"):
                judge_score = 0.7 * judge_score + 0.3 * pres.raw_score
            final = Decision.BLOCK if judge_score >= 0.5 else Decision.PASS
            gd.rationale = verdict.rationale if verdict else (
                "escalated; judge degraded" if jres.metadata.get("degraded")
                else "escalated")
        latency = (time.perf_counter() - start) * 1000
        response = DetectResponse(
            decision=final,
            scores=scores,
            disagreement=gd.disagreement,
            rationale=gd.rationale,
            escalated=escalated,
            latency_ms=latency,
        )
        audit = AuditLogRecord(
            prompt_hash=hashlib.sha256(text.encode()).hexdigest(),
            decision=final,
            scores=scores,
            disagreement=gd.disagreement,
            escalated=escalated,
            rationale=gd.rationale,
            judge_verdict=verdict,
            policy_mode=self.settings.policy_mode,
            latency_ms=latency,
        )
        meta = {"degraded": degraded_any,
                "channel_latency": {n: r.latency_ms for n, r in results.items()}}
        return response, audit, meta
