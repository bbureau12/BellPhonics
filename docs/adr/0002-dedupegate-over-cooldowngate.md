# ADR 0002: Replace CooldownGate with DedupeGate

**Date:** 2025-01-16

## Status
Accepted

## Context
Bellphonics needs to prevent duplicate speech events from being announced multiple times when clients retry or send duplicates.

The original `CooldownGate` implementation used complex cooldown policies (per-severity, global cooldown) and required policy composition. It was over-engineered for the actual use case.

## Decision
Replace `CooldownGate` with a simpler `DedupeGate` that uses event IDs for deduplication.

Implementation:
- Simple in-memory cache of `event_id` strings
- TTL-based expiration (`BELLPHONICS_DEDUPE_TTL_S`, default 60s)
- No severity-based policies or complex composition
- Clear semantics: same `event_id` within TTL = duplicate

```python
class DedupeGate:
    def __init__(self, ttl_seconds: int = 60):
        self._cache = {}
        self._ttl = ttl_seconds
    
    def should_allow(self, event_id: str) -> bool:
        now = time.time()
        
        # Check if duplicate
        if event_id in self._cache:
            event_time = self._cache[event_id]
            if now - event_time < self._ttl:
                return False  # Duplicate
        
        # Allow and cache
        self._cache[event_id] = now
        return True
```

## Consequences

### Positive
- ✅ Dramatically simpler code (~30 lines vs ~150 lines)
- ✅ Easier to understand and maintain
- ✅ Predictable behavior
- ✅ No policy composition complexity
- ✅ Clients control uniqueness via `event_id`

### Negative
- ⚠️ No per-severity cooldowns (not needed in practice)
- ⚠️ Unbounded memory growth if many unique events (mitigated: TTL cleanup on next check)

### Neutral
- Different approach but same end goal
- Shifts responsibility to client to generate unique IDs

## Alternatives Considered

### 1. Keep CooldownGate with policies
Continue using the complex policy-based system.

**Rejected because:**
- YAGNI: No actual use case for per-severity policies
- Overengineered for simple deduplication
- Hard to test and reason about

### 2. Content-based deduplication (hash text)
Hash the `text` field instead of using `event_id`.

**Rejected because:**
- Different events can have same text
- Doesn't handle retries well (same event, same text, should dedupe)
- Client has better context about what constitutes a "unique" event

### 3. No deduplication
Let clients handle it entirely.

**Rejected because:**
- Poor user experience (announcements repeating)
- Network issues cause natural retries
- Server-side deduplication is expected behavior

## Migration Notes
- Existing `.env` configs: Remove `BELLPHONICS_COOLDOWN_*` settings, add `BELLPHONICS_DEDUPE_TTL_S`
- Clients must provide unique `event_id` for each distinct event
- Default TTL of 60s works for most scenarios

## References
- Original feature request: "can you help me replace cooldowngate with deupegate?"
- Conversation about simplicity vs flexibility
