from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from .models import SpeechEvent
from .tts.base import TTSEngine

log = logging.getLogger("bellphonics.queue")


@dataclass(frozen=True)
class SpeakJob:
    event: SpeechEvent


class SpeechQueue:
    def __init__(self, engine: TTSEngine):
        self.engine = engine
        self.q: asyncio.Queue[SpeakJob] = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        if self._task is not None:
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            await asyncio.sleep(0)  # yield
            self._task.cancel()
            self._task = None

    async def enqueue(self, event: SpeechEvent) -> None:
        await self.q.put(SpeakJob(event=event))

    async def _worker(self) -> None:
        while not self._stop.is_set():
            job = await self.q.get()
            try:
                e = job.event
                log.info("Speaking event_id=%s severity=%s room=%s", e.event_id, e.severity, e.room)
                self.engine.speak(e.text, voice=e.voice, volume=e.volume)
            except Exception:
                log.exception("Speech worker error")
            finally:
                self.q.task_done()
