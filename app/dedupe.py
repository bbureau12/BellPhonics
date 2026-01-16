from __future__ import annotations

import time


class DedupeGate:
    """
    Minimal safety: prevent re-speaking the exact same event_id.
    No cooldown logic; that belongs upstream (EchoBell).
    """

    def __init__(self, *, ttl_s: int = 600):
        self.ttl_s = ttl_s
        self._seen: dict[str, float] = {}  # event_id -> seen_ts

    def _gc(self) -> None:
        now = time.time()
        expired = [eid for eid, ts in self._seen.items() if (now - ts) > self.ttl_s]
        for eid in expired:
            self._seen.pop(eid, None)

    def allow(self, event_id: str) -> bool:
        now = time.time()
        self._gc()

        if event_id in self._seen:
            return False

        self._seen[event_id] = now
        return True
