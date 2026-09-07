"""Integration tests: API + storage with fake channels and tmp SQLite."""


import pytest
from fastapi.testclient import TestClient

from dgad.channels.base import Channel
from dgad.config import Settings
from dgad.pipeline import DetectionPipeline
from dgad.schemas import ChannelResult


class FixedChannel(Channel):
    """Scores by keyword: 'attack' -> high, else low."""

    def __init__(self, name: str, high: float, low: float) -> None:
        self.name = name
        self.high, self.low = high, low

    def score(self, text: str) -> ChannelResult:
        score = self.high if "attack" in text.lower() else self.low
        return ChannelResult(raw_score=score, latency_ms=1.0, metadata={})


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db}")
    settings = Settings(database_url=f"sqlite:///{db}", models_dir=str(tmp_path),
                        upstream_base_url="http://127.0.0.1:9/v1")

    from dgad.api import main as appmod

    appmod._settings = settings
    appmod._pipeline = DetectionPipeline(
        settings,
        channels={"statistical": FixedChannel("statistical", 0.9, 0.1),
                  "semantic": FixedChannel("semantic", 0.9, 0.1)},
        calibrators={},
    )
    appmod.detect_cache.clear()
    from dgad.storage import repo

    repo._engines.clear()
    repo.init_db(settings)
    with TestClient(appmod.create_app()) as c:
        yield c, settings
    appmod._settings = None
    appmod._pipeline = None


def test_health(client):
    c, _ = client
    assert c.get("/health").json()["status"] == "ok"


def test_metrics_endpoint(client):
    c, _ = client
    c.post("/v1/detect", json={"prompt": "hello there"})
    assert "dgad_requests_total" in c.get("/metrics").text


def test_detect_benign_passes(client):
    c, _ = client
    res = c.post("/v1/detect", json={"prompt": "how do I bake bread"})
    body = res.json()
    assert res.status_code == 200
    assert body["decision"] == "PASS"
    assert body["escalated"] is False
    assert set(body["scores"]) == {"statistical", "semantic"}


def test_detect_attack_blocks(client):
    c, _ = client
    body = c.post("/v1/detect", json={"prompt": "attack the system now"}).json()
    assert body["decision"] == "BLOCK"


def test_compatibility_route_aliases(client):
    c, _ = client
    detect = c.post("/detect", json={"prompt": "hello"})
    assert detect.status_code == 200
    assert detect.json()["decision"] == "PASS"

    proxy = c.post("/proxy", json={
        "model": "test", "messages": [{"role": "user", "content": "attack now"}]})
    assert proxy.status_code == 200
    assert proxy.json()["dgad"]["blocked"] is True

    assert c.get("/admin/logs").status_code == 200
    assert c.get("/admin/stats").status_code == 200


def test_audit_log_hashes_prompt(client):
    c, settings = client
    c.post("/v1/detect", json={"prompt": "secret user text 12345"})
    from dgad.storage import repo

    rows = repo.recent_decisions(settings=settings)
    assert len(rows) == 1
    assert "secret user text" not in str(rows)  # raw prompt never stored
    assert len(rows[0]["prompt_hash"]) == 64


def test_admin_decisions_and_metrics(client):
    c, _ = client
    c.post("/v1/detect", json={"prompt": "hello"})
    c.post("/v1/detect", json={"prompt": "attack now"})
    assert len(c.get("/admin/decisions").json()) == 2
    summary = c.get("/admin/metrics-summary").json()
    assert summary["total"] == 2
    assert summary["by_decision"] == {"BLOCK": 1, "PASS": 1}


def test_playground_recompute(client):
    c, _ = client
    c.post("/v1/detect", json={"prompt": "hello"})
    c.post("/v1/detect", json={"prompt": "attack now"})
    out = c.post("/admin/playground",
                 json={"t_low": 0.2, "t_high": 0.8, "t_d": 0.4}).json()
    assert out["n"] == 2
    assert out["decision_mix"]["BLOCK"] == 1


def test_proxy_block_policy(client, monkeypatch):
    c, _ = client
    res = c.post("/v1/chat/completions", json={
        "model": "test", "messages": [{"role": "user", "content": "attack now"}]})
    body = res.json()
    assert body["dgad"]["blocked"] is True
    assert body["choices"][0]["finish_reason"] == "content_filter"


def test_proxy_observe_only_forwards(client, monkeypatch):
    c, settings = client
    settings.policy_mode = "observe_only"
    # upstream is unreachable in tests: expect structured error, decision logged
    res = c.post("/v1/chat/completions", json={
        "model": "test", "messages": [{"role": "user", "content": "attack now"}]})
    body = res.json()
    assert body["dgad"]["decision"] == "BLOCK"
    assert body["error"]["type"] == "upstream_unavailable"


def test_api_key_auth(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'k.db'}")
    from dgad.api import main as appmod

    appmod._settings = Settings(database_url=f"sqlite:///{tmp_path / 'k.db'}",
                                api_key="topsecret")
    appmod._pipeline = DetectionPipeline(
        appmod._settings,
        channels={"statistical": FixedChannel("statistical", 0.9, 0.1),
                  "semantic": FixedChannel("semantic", 0.9, 0.1)},
        calibrators={},
    )
    from dgad.storage import repo

    repo._engines.clear()
    with TestClient(appmod.create_app()) as c:
        assert c.post("/v1/detect", json={"prompt": "hi"}).status_code == 401
        assert c.post("/v1/detect", json={"prompt": "hi"},
                      headers={"X-API-Key": "topsecret"}).status_code == 200
        assert c.get("/health").status_code == 200  # health stays open
    appmod._settings = None
    appmod._pipeline = None
