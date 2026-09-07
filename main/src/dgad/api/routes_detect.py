"""POST /v1/detect: score a prompt without forwarding it anywhere."""

from fastapi import APIRouter, Depends

from dgad.api import main as appmod
from dgad.normalise import normalise
from dgad.pipeline import DetectionPipeline
from dgad.schemas import DetectRequest, DetectResponse
from dgad.storage import repo

router = APIRouter()


@router.post("/detect", response_model=DetectResponse, include_in_schema=False)
@router.post("/v1/detect", response_model=DetectResponse)
def detect(req: DetectRequest,
           pipeline: DetectionPipeline = Depends(appmod.get_pipeline)) -> DetectResponse:
    settings = appmod.get_app_settings()
    key = repo.hash_prompt(normalise(req.prompt))
    cached = appmod.detect_cache.get(key)
    if cached is not None:
        return cached
    response, audit, meta = pipeline.detect(req.prompt)
    repo.insert_decision(audit, channel_latency=meta["channel_latency"],
                         degraded=meta["degraded"], settings=settings)
    appmod.REQUESTS.labels(decision=response.decision.value).inc()
    appmod.LATENCY.observe(response.latency_ms)
    if response.escalated:
        appmod.ESCALATIONS.inc()
    appmod.detect_cache.put(key, response)
    appmod.log.info("detect", decision=response.decision.value,
                    escalated=response.escalated,
                    latency_ms=round(response.latency_ms, 2))
    return response
