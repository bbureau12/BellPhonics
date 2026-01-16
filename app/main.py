from __future__ import annotations

import logging
from fastapi import Depends, FastAPI, Header, HTTPException
from dotenv import load_dotenv

from .config import load_settings, Settings
from .dedupe import DedupeGate
from .queue import SpeechQueue
from .tts.mock import MockTTS

from . import api

log = logging.getLogger("bellphonics")


def create_app() -> FastAPI:
    load_dotenv()
    settings = load_settings()

    # TTS backend selection (v1: mock only)
    engine = MockTTS()
    if settings.tts_backend == "sapi":
        from .tts.sapi import WindowsSapiTTS
        engine = WindowsSapiTTS()
    elif settings.tts_backend == "piper":
        from .tts.piper import PiperTTS
        engine = PiperTTS(model_path=settings.piper_model)

    gate = DedupeGate(ttl_s=settings.dedupe_ttl_s)
    speech_queue = SpeechQueue(engine=engine)

    app = FastAPI(title="Bellphonics", version="0.1.0")

    # Dependencies
    def get_settings() -> Settings:
        return settings

    def get_gate() -> DedupeGate:
        return gate

    def get_queue() -> SpeechQueue:
        return speech_queue

    def require_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
        if not x_api_key or x_api_key.strip() != settings.api_key:
            raise HTTPException(status_code=401, detail="Unauthorized")

    # Wire router dependencies
    api.router.dependency_overrides_provider = app  # ok to leave
    app.dependency_overrides[api.get_settings] = get_settings
    app.dependency_overrides[api.get_gate] = get_gate
    app.dependency_overrides[api.get_queue] = get_queue

    # Apply auth to /speak only
    app.include_router(api.router, dependencies=[])

    # Add an auth-protected route wrapper:
    # (FastAPI doesn't let us apply per-route dependencies after include easily without duplication,
    # so simplest is to re-declare /speak here as a mounted dependency.)
    # Instead: enforce auth globally EXCEPT /health by adding a middleware.
    # For v1, we'll do a global dependency and carve out /health with an exception.

    @app.middleware("http")
    async def api_key_middleware(request, call_next):
        # allow health without auth
        if request.url.path == "/health":
            return await call_next(request)

        # require key for everything else
        key = request.headers.get("X-API-Key")
        if not key or key.strip() != settings.api_key:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        return await call_next(request)

    @app.on_event("startup")
    async def _startup():
        logging.basicConfig(level=logging.INFO)
        await speech_queue.start()
        log.info("Bellphonics started")

    @app.on_event("shutdown")
    async def _shutdown():
        await speech_queue.stop()
        log.info("Bellphonics stopped")

    return app


app = create_app()
