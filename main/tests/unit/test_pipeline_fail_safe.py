"""Focused fail-safe tests for required and escalation channels."""

from dgad.channels.base import Channel
from dgad.config import Settings
from dgad.pipeline import DetectionPipeline
from dgad.schemas import ChannelResult, Decision


class FixedChannel(Channel):
    def __init__(self, name: str, score: float, *, degraded: bool = False,
                 verdict: dict | None = None) -> None:
        self.name = name
        self._score = score
        self._degraded = degraded
        self._verdict = verdict

    def score(self, text: str) -> ChannelResult:
        metadata = {"degraded": self._degraded}
        if self._verdict is not None:
            metadata["verdict"] = self._verdict
        return ChannelResult(raw_score=self._score, latency_ms=1.0, metadata=metadata)


def _settings(tmp_path) -> Settings:
    return Settings(models_dir=str(tmp_path))


def test_degraded_judge_and_healthy_low_probe_cannot_pass(tmp_path):
    pipeline = DetectionPipeline(
        _settings(tmp_path),
        channels={
            "statistical": FixedChannel("statistical", 0.1),
            "semantic": FixedChannel("semantic", 0.9),
        },
        calibrators={},
        judge=FixedChannel("judge", 0.0, degraded=True),
        probe=FixedChannel("behavioural", 0.0),
    )

    response, _, meta = pipeline.detect("contested prompt")

    assert response.escalated is True
    assert response.decision is Decision.BLOCK
    assert response.degraded is True
    assert response.metadata["escalation_degraded"] is True
    assert meta["escalation_degraded"] is True
    assert response.channel_results["judge"].metadata["degraded"] is True


def test_missing_required_semantic_channel_fails_closed(tmp_path):
    pipeline = DetectionPipeline(
        _settings(tmp_path),
        channels={"statistical": FixedChannel("statistical", 0.05)},
        calibrators={},
        judge=FixedChannel("judge", 0.5, degraded=True),
        probe=FixedChannel("behavioural", 0.5, degraded=True),
    )

    response, _, _ = pipeline.detect("apparently benign")

    assert response.escalated is True
    assert response.decision is Decision.BLOCK
    assert response.metadata["missing_required_channels"] == ["semantic"]


def test_response_exposes_raw_and_calibrated_channel_details(tmp_path):
    pipeline = DetectionPipeline(
        _settings(tmp_path),
        channels={
            "statistical": FixedChannel("statistical", 0.1),
            "semantic": FixedChannel("semantic", 0.2),
        },
        calibrators={},
    )

    response, _, _ = pipeline.detect("benign prompt")

    assert response.decision is Decision.PASS
    assert response.channel_results["statistical"].raw_score == 0.1
    assert response.channel_results["statistical"].calibrated_score is None
    assert response.degraded is False
