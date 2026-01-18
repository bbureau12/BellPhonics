from __future__ import annotations

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
import logging
import os

from .config import load_settings, Settings
from .dedupe import DedupeGate
from .discovery import DiscoveryConfig, MdnsAdvertiser
from .queue import SpeechQueue
from .security import SecurityConfig, SecurityGate
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
        engine = PiperTTS(
            voices_dir=settings.piper_voices_dir,
            default_voice=settings.piper_default_voice,
        )

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
    allow = os.getenv("BELLPHONICS_ALLOWLIST", "").strip()
    allowlist = {ip.strip() for ip in allow.split(",") if ip.strip()}
    sec = SecurityGate(SecurityConfig(
        api_key=settings.api_key,
        allowlist=allowlist,
        rate_limit_per_min=int(os.getenv("BELLPHONICS_RATE_LIMIT_PER_MIN", "20")),
        dedupe_ttl_s=settings.dedupe_ttl_s,
    ))
    advertiser = MdnsAdvertiser(
        DiscoveryConfig(
            enabled=(os.getenv("BELLPHONICS_DISCOVERY_ENABLED", "false").lower() == "true"),
            instance_name=os.getenv("BELLPHONICS_DISCOVERY_NAME", "Bellphonics"),
            host=os.getenv("BELLPHONICS_DISCOVERY_HOST", ""),
            zone=os.getenv("BELLPHONICS_DISCOVERY_ZONE", ""),
            subzone=os.getenv("BELLPHONICS_DISCOVERY_SUBZONE", ""),
            port=settings.bind_port,
            txt={
                "service": "bellphonics",
                "version": "0.1.0",
                "path": "/speak",
            },
        )
    )

    @app.middleware("http")
    async def security_middleware(request, call_next):
        resp = sec.middleware(request)
        if resp is not None:
            return resp
        return await call_next(request)

    @app.on_event("startup")
    async def _startup():
        logging.basicConfig(level=logging.INFO)
        await speech_queue.start()
        await advertiser.start()
        log.info("Bellphonics started")

    @app.on_event("shutdown")
    async def _shutdown():
        await advertiser.stop()
        await speech_queue.stop()
        log.info("Bellphonics stopped")

    return app


app = create_app()
