from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class GateResult:
    allowed: bool
    reason: str


class CooldownGate:
    """
    Keeps Bellphonics calm:
    - replay protection (event_id)
    - cooldowns (cooldown_key)
    """

    def __init__(self, *, dedupe_ttl_s: int):
        self.dedupe_ttl_s = dedupe_ttl_s
        self._seen_event: dict[str, float] = {}     # event_id -> seen_ts
        self._cooldowns: dict[str, float] = {}      # cooldown_key -> last_spoken_ts

    def _gc(self) -> None:
        now = time.time()
        # purge old event IDs
        expired = [eid for eid, ts in self._seen_event.items() if (now - ts) > self.dedupe_ttl_s]
        for eid in expired:
            self._seen_event.pop(eid, None)

    def allow(self, *, event_id: str, cooldown_key: str | None, cooldown_s: int) -> GateResult:
        now = time.time()
        self._gc()

        if event_id in self._seen_event:
            return GateResult(False, "duplicate_event")

        if cooldown_key:
            last = self._cooldowns.get(cooldown_key)
            if last is not None and (now - last) < cooldown_s:
                return GateResult(False, "cooldown")

        # mark
        self._seen_event[event_id] = now
        if cooldown_key:
            self._cooldowns[cooldown_key] = now

        return GateResult(True, "ok")
