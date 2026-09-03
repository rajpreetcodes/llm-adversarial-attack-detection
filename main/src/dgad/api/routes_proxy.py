"""POST /v1/chat/completions: OpenAI-compatible proxy with detection in front.

Point any existing OpenAI client at this base URL and detection happens
invisibly in between. Policy modes: block (refuse), flag_and_pass (forward
with a header), observe_only (log only, enforce nothing: how real security
products are rolled out before enforcement is switched on).
"""

import hashlib
from typing import Any

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from dgad.api import main as appmod
from dgad.pipeline import DetectionPipeline
from dgad.schemas import Decision
from dgad.storage import repo

router = APIRouter()


class ChatRequest(BaseModel):
    """Subset of the OpenAI chat-completions schema we need to inspect."""

    model: str = "unknown"
    messages: list[dict[str, Any]]
    stream: bool = False


def _last_user_message(req: ChatRequest) -> str:
    for msg in reversed(req.messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            return content if isinstance(content, str) else str(content)
    return ""


def _refusal(model: str, rationale: str | None) -> dict:
    return {
        "id": "dgad-blocked",
        "object": "chat.completion",
        "model": model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": ("This prompt was blocked by the DGAD security layer. "
                            + (f"Reason: {rationale}" if rationale else "")),
            },
            "finish_reason": "content_filter",
        }],
        "dgad": {"blocked": True},
    }


@router.post("/v1/chat/completions")
async def chat_completions(
    req: ChatRequest,
    pipeline: DetectionPipeline = Depends(appmod.get_pipeline),
) -> dict:
    settings = appmod.get_app_settings()
    prompt = _last_user_message(req)
    response, audit, meta = pipeline.detect(prompt or "(empty)")
    repo.insert_decision(audit, channel_latency=meta["channel_latency"],
                         degraded=meta["degraded"], settings=settings)
    appmod.REQUESTS.labels(decision=response.decision.value).inc()
    blocked = response.decision is Decision.BLOCK
    if blocked and settings.policy_mode == "block":
        return _refusal(req.model, response.rationale)
    # flag_and_pass and observe_only both forward; flag mode marks it
    upstream = f"{settings.upstream_base_url.rstrip('/')}/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(upstream, json=req.model_dump())
        body = resp.json()
    except httpx.HTTPError as exc:
        return {"error": {"type": "upstream_unavailable", "message": str(exc)},
                "dgad": {"decision": response.decision.value}}
    body["dgad"] = {
        "decision": response.decision.value,
        "flagged": blocked and settings.policy_mode == "flag_and_pass",
        "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
    }
    return body
