# ADR 0001: Use AsyncZeroconf for mDNS Service Discovery

**Date:** 2025-01-16

## Status
Accepted

## Context
Bellphonics needs mDNS/Bonjour service advertisement to allow clients (like EchoBell) to discover it on the local network without manual configuration.

The standard `zeroconf` Python package provides synchronous service registration, but our application uses FastAPI with async/await throughout. Running synchronous Zeroconf in an async context causes `EventLoopBlocked` warnings and potential deadlocks.

## Decision
Use `zeroconf.asyncio.AsyncZeroconf` instead of synchronous `Zeroconf`.

Implementation:
- `MdnsAdvertiser` in `app/discovery.py` uses `AsyncZeroconf()`
- `async_register_service()` and `async_unregister_all_services()` instead of sync methods
- Proper `await aiozc.async_close()` cleanup on shutdown
- Integrated with FastAPI lifespan events (`@app.on_event("startup")`, `@app.on_event("shutdown")`)

## Consequences

### Positive
- ✅ No event loop blocking warnings
- ✅ Non-blocking service registration during app startup
- ✅ Consistent async/await patterns throughout codebase
- ✅ Proper resource cleanup with async context managers

### Negative
- ⚠️ Slightly more complex API than synchronous version
- ⚠️ Requires understanding of async context managers

### Neutral
- Same `zeroconf` package, just using async API
- No additional dependencies

## Alternatives Considered

### 1. Synchronous Zeroconf with threading
Run synchronous Zeroconf in a separate thread using `asyncio.to_thread()`.

**Rejected because:**
- Adds threading complexity
- Requires thread-safe communication with main event loop
- Still generates event loop warnings

### 2. No mDNS, manual configuration only
Require users to manually configure client IP/port.

**Rejected because:**
- Poor user experience
- One of the project's key features is auto-discovery
- Manual config error-prone in DHCP environments

## References
- [python-zeroconf AsyncZeroconf docs](https://python-zeroconf.readthedocs.io/en/latest/async.html)
- [FastAPI lifespan events](https://fastapi.tiangolo.com/advanced/events/)
