from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


Severity = Literal["debug", "info", "warn", "alert"]


class SpeechEvent(BaseModel):
    event_id: str = Field(..., min_length=8)
    ts: float

    text: str = Field(..., min_length=1, max_length=240)
    severity: Severity = "info"

    room: Optional[str] = None

    cooldown_key: Optional[str] = None
    cooldown_s: Optional[int] = Field(default=None, ge=0, le=3600)

    voice: Optional[str] = None
    volume: Optional[float] = Field(default=None, ge=0.0, le=1.0)
