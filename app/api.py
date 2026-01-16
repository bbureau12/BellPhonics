from __future__ import annotations

from fastapi import APIRouter, Depends
from .config import Settings
from .auth import require_api_key
from .models import SpeechEvent
from .cooldown import CooldownGate
from .queue import SpeechQueue

router = APIRouter()


def get_settings() -> Settings:
    # injected by main.py via router dependency override, but safe default:
    raise RuntimeError("Settings dependency not wired")


def get_gate() -> CooldownGate:
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
    gate: CooldownGate = Depends(get_gate),
    q: SpeechQueue = Depends(get_queue),
    _: None = Depends(lambda x_api_key=None: None),  # placeholder for FastAPI signature
):
    # auth (done explicitly so we can pass settings)
    # Note: FastAPI won't inject settings into require_api_key directly; do it manually:
    from fastapi import Header
    # (We can’t inject Header here cleanly without repetition, so we do it in main with a dependency.)
    # This function assumes auth already ran.

    cooldown_s = event.cooldown_s if event.cooldown_s is not None else settings.default_cooldown_s
    res = gate.allow(event_id=event.event_id, cooldown_key=event.cooldown_key, cooldown_s=cooldown_s)

    if not res.allowed:
        return {"ok": True, "accepted": False, "reason": res.reason}

    await q.enqueue(event)
    return {"ok": True, "accepted": True}
