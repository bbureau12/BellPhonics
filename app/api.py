from __future__ import annotations

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


@router.get("/health")
def health() -> dict:
    return {"ok": True}


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
