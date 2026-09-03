"""FastAPI application: detection API, OpenAI-compatible proxy, admin routes."""

import time
from collections import OrderedDict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from dgad.config import Settings, get_settings
from dgad.pipeline import DetectionPipeline
from dgad.storage import repo

structlog.configure(processors=[structlog.processors.JSONRenderer()])
log = structlog.get_logger("dgad")

REQUESTS = Counter("dgad_requests_total", "Detection requests", ["decision"])
LATENCY = Histogram("dgad_latency_ms", "End-to-end detection latency (ms)")
ESCALATIONS = Counter("dgad_escalations_total", "Prompts sent to the escalation tier")

_settings: Settings | None = None
_pipeline: DetectionPipeline | None = None


class BoundedCache(OrderedDict):
    """In-process detection cache when Redis is not configured."""

    def __init__(self, maxsize: int = 4096) -> None:
        super().__init__()
        self.maxsize = maxsize

    def put(self, key: str, value: Any) -> None:
        self[key] = value
        if len(self) > self.maxsize:
            self.popitem(last=False)


detect_cache = BoundedCache()


def get_app_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings


def get_pipeline() -> DetectionPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = DetectionPipeline(get_app_settings())
    return _pipeline


def require_api_key(request: Request,
                    settings: Settings = Depends(get_app_settings)) -> None:
    """API-key auth; disabled when DGAD_API_KEY/api_key is unset (dev only)."""
    if settings.api_key is None:
        return
    if request.headers.get("X-API-Key") != settings.api_key:
        raise HTTPException(status_code=401, detail="invalid or missing API key")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_app_settings()
    repo.init_db(settings)
    log.info("startup", database=settings.database_url, policy=settings.policy_mode)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="DGAD", version="0.1.0", lifespan=lifespan)

    from dgad.api import routes_admin, routes_detect, routes_proxy

    app.include_router(routes_detect.router, dependencies=[Depends(require_api_key)])
    app.include_router(routes_proxy.router, dependencies=[Depends(require_api_key)])
    app.include_router(routes_admin.router, dependencies=[Depends(require_api_key)])

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "time": time.time()}

    @app.get("/metrics")
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
