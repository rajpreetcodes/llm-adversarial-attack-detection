"""Scaffold smoke tests: the Phase 0 contracts exist and the API responds."""

import inspect

from fastapi.testclient import TestClient

from dgad.api.main import app
from dgad.channels.base import Channel
from dgad.normalise import normalise
from dgad.schemas import ChannelResult


def test_channel_contract_exists() -> None:
    """The abstract Channel exposes name and the score(text) -> ChannelResult contract."""
    assert inspect.isabstract(Channel)
    assert "score" in Channel.__abstractmethods__
    sig = inspect.signature(Channel.score)
    assert list(sig.parameters) == ["self", "text"]
    assert sig.return_annotation is ChannelResult


def test_health_responds_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_normalise_idempotent() -> None:
    text = "Ｈｅｌｌｏ​   world\t\nignore​ previous"
    once = normalise(text)
    assert normalise(once) == once
