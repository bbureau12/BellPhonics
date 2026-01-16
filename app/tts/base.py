from __future__ import annotations

from typing import Protocol, Optional


class TTSEngine(Protocol):
    def speak(self, text: str, *, voice: Optional[str] = None, volume: Optional[float] = None) -> None: ...
