# Architecture Decision Records (ADR)

This directory contains records of architectural decisions made during Bellphonics development.

## Format
ADRs follow a lightweight format:
- **Status:** Accepted | Rejected | Superseded | Deprecated
- **Context:** What problem are we solving?
- **Decision:** What did we decide?
- **Consequences:** What are the trade-offs?
- **Alternatives Considered:** What else did we think about?

## Index

### [ADR-0001: Use AsyncZeroconf for mDNS Service Discovery](0001-async-zeroconf-for-mdns.md)
**Status:** Accepted  
**Date:** 2025-01-16  
Use `AsyncZeroconf` instead of synchronous `Zeroconf` to avoid event loop blocking in async FastAPI application.

### [ADR-0002: Replace CooldownGate with DedupeGate](0002-dedupegate-over-cooldowngate.md)
**Status:** Accepted  
**Date:** 2025-01-16  
Use simple event ID-based deduplication instead of complex cooldown policies.

### [ADR-0003: DNS Allowlist with Resolution Caching](0003-dns-allowlist-with-caching.md)
**Status:** Accepted  
**Date:** 2025-01-16  
Support DNS hostnames (e.g., `echobell.local`) in allowlist with 5-minute resolution caching.

### [ADR-0004: Multi-Voice Architecture with Directory-Based Loading](0004-multi-voice-directory-loading.md)
**Status:** Accepted  
**Date:** 2025-01-16  
Load Piper voices on-demand from a directory with caching, rather than single model or pre-loading all.

### [ADR-0005: Public Handshake Endpoint for Discovery Integration](0005-public-handshake-endpoint.md)
**Status:** Accepted  
**Date:** 2025-01-16  
Provide unauthenticated `/handshake` endpoint for capability discovery and version negotiation.

---

## Creating New ADRs

1. Copy the template from the most recent ADR
2. Number sequentially (e.g., `0006-your-decision.md`)
3. Fill in all sections
4. Update this index
5. Reference related ADRs in the "References" section
