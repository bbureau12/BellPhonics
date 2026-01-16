from __future__ import annotations

import logging
from typing import Optional

log = logging.getLogger("bellphonics.tts.mock")


class MockTTS:
    def speak(self, text: str, *, voice: Optional[str] = None, volume: Optional[float] = None) -> None:
        log.info("[MOCK SPEAK] voice=%s volume=%s text=%r", voice, volume, text)
