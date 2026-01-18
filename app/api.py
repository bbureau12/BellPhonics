from __future__ import annotations

import os
from pathlib import Path
from fastapi import APIRouter, Depends
from .config import Settings
from .auth import require_api_key
from .models import SpeechEvent
from .dedupe import DedupeGate
from .queue import SpeechQueue

router = APIRouter()


def get_settings() -> Settings:
    # injected by main.py via router dependency override, but safe default:
    raise RuntimeError("Settings dependency not wired")


def get_gate() -> DedupeGate:
    raise RuntimeError("Gate dependency not wired")


def get_queue() -> SpeechQueue:
    raise RuntimeError("Queue dependency not wired")


def _get_available_voices(voices_dir: str) -> list[str]:
    """Scan the voices directory for available .onnx files."""
    voices_path = Path(voices_dir)
    if not voices_path.exists():
        return []
    
    # Find all .onnx files and extract voice names (without .onnx extension)
    return sorted([
        f.stem  # filename without extension
        for f in voices_path.glob("*.onnx")
    ])


@router.get("/health")
def health() -> dict:
    return {"ok": True}


@router.get("/handshake")
def handshake(settings: Settings = Depends(get_settings)) -> dict:
    """
    Returns discovery and TTS configuration information.
    Useful for clients to verify connectivity and understand server capabilities.
    """
    tts_info = {
        "backend": settings.tts_backend,
    }
    
    if settings.tts_backend == "piper":
        tts_info["piper"] = {
            "voices_dir": settings.piper_voices_dir,
            "default_voice": settings.piper_default_voice,
            "available_voices": _get_available_voices(settings.piper_voices_dir),
        }
    
    return {
        "ok": True,
        "discovery": {
            "enabled": os.getenv("BELLPHONICS_DISCOVERY_ENABLED", "false").lower() == "true",
            "instance_name": os.getenv("BELLPHONICS_DISCOVERY_NAME", "Bellphonics"),
            "host": os.getenv("BELLPHONICS_DISCOVERY_HOST", ""),
            "zone": os.getenv("BELLPHONICS_DISCOVERY_ZONE", ""),
            "subzone": os.getenv("BELLPHONICS_DISCOVERY_SUBZONE", ""),
            "port": settings.bind_port,
        },
        "tts": tts_info,
        "version": "0.1.0",
    }


@router.post("/speak")
async def speak(
    event: SpeechEvent,
    settings: Settings = Depends(get_settings),
    gate: DedupeGate = Depends(get_gate),
    q: SpeechQueue = Depends(get_queue),
    _: None = Depends(lambda x_api_key=None: None),  # placeholder for FastAPI signature
):
    # auth (done explicitly so we can pass settings)
    # Note: FastAPI won't inject settings into require_api_key directly; do it manually:
    from fastapi import Header
    # (We can’t inject Header here cleanly without repetition, so we do it in main with a dependency.)
    # This function assumes auth already ran.

    if not gate.allow(event.event_id):
        return {"ok": True, "accepted": False, "reason": "duplicate_event"}

    await q.enqueue(event)
    return {"ok": True, "accepted": True}
