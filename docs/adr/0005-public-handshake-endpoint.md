# ADR 0005: Public Handshake Endpoint for Discovery Integration

**Date:** 2025-01-16

## Status
Accepted

## Context
Bellphonics uses mDNS to advertise its presence on the network. Clients like EchoBell discover the service via mDNS and need to:
1. Verify the server is actually Bellphonics (not another service on same port)
2. Query server capabilities (available voices, configuration)
3. Determine API version compatibility

However, mDNS only provides IP, port, and basic TXT records. Clients need a lightweight API endpoint to "handshake" and get full configuration details.

## Decision
Create a public `/handshake` GET endpoint that returns server configuration and capabilities **without requiring authentication**.

**Endpoint:** `GET /handshake`

**Response:**
```json
{
  "ok": true,
  "discovery": {
    "enabled": true,
    "instance_name": "Bellphonics",
    "host": "bellphonics",
    "zone": "home",
    "subzone": "kitchen",
    "port": 8099
  },
  "tts": {
    "backend": "piper",
    "piper": {
      "voices_dir": "app/tts/voicepacks",
      "default_voice": "en_GB-alba-medium",
      "available_voices": [
        "en_GB-alba-medium",
        "en_GB-jenny_dioco-medium"
      ]
    }
  },
  "version": "0.1.0"
}
```

**Security Exception:**
- `/handshake` is exempt from API key and allowlist checks
- Listed alongside `/health` in `SecurityGate` middleware

## Consequences

### Positive
- ✅ Clients can verify service identity before authenticating
- ✅ Voice selection UI can query available voices dynamically
- ✅ Zero-config client setup: mDNS → handshake → cached config
- ✅ Version negotiation possible (client checks `version` field)
- ✅ Useful for debugging (curl http://server:8099/handshake)

### Negative
- ⚠️ Information disclosure: reveals server config to unauthenticated clients
- ⚠️ Available voices list reveals installed models
- ⚠️ Discovery settings expose network topology (zone/subzone)

### Risk Mitigation
- **Low risk in practice:** Bellphonics is designed for trusted local networks, not internet exposure
- Information disclosed is non-sensitive (voice names, zone labels)
- No credentials, API keys, or allowlist IPs are exposed
- Actual `/speak` endpoint still requires authentication

## Alternatives Considered

### 1. Require authentication for /handshake
Apply same security as `/speak` endpoint.

**Rejected because:**
- Chicken-and-egg: client needs to know capabilities before configuring auth
- Forces hardcoded voice names in client config
- Defeats purpose of dynamic discovery
- mDNS already reveals IP and port (no additional disclosure)

### 2. Embed all info in mDNS TXT records
Put voice list, version, etc. in TXT records.

**Rejected because:**
- TXT record size limits (255 bytes per string, ~400 bytes total typical)
- Voice list can be large (10+ voices × 30 chars = 300 bytes)
- Can't update dynamically without re-registering service
- Awkward encoding (comma-separated strings)

### 3. Two-tier handshake (public basic, auth for details)
Public endpoint returns basic info, authenticated endpoint returns full details.

**Rejected because:**
- Overengineered for local network use case
- Voice list is needed before authentication setup
- Adds API complexity for minimal security gain

### 4. No handshake, rely on mDNS alone
Clients hardcode assumptions about server capabilities.

**Rejected because:**
- Breaks when server config changes (new voices added, etc.)
- Version incompatibility issues
- Poor client UX

## Security Considerations
- **Threat model:** Bellphonics operates on trusted local networks (home LANs)
- **Exposure:** Handshake reveals what an attacker could learn via mDNS + port scan anyway
- **Sensitive data:** Not present in handshake response (no API keys, no allowlist, no file paths beyond voice dir name)
- **Rate limiting:** Not applied (stateless, read-only, cheap to compute)
- **DoS risk:** Minimal (simple JSON serialization, no DB queries)

## Client Integration Flow
1. Client discovers `_bellphonics._tcp.local.` via mDNS
2. Client extracts IP and port from mDNS response
3. Client sends `GET http://<ip>:<port>/handshake`
4. Client validates `ok: true` and `version` compatibility
5. Client caches `available_voices` and `default_voice`
6. Client prompts user for API key (or loads from config)
7. Client sends authenticated requests to `/speak`

## Migration Notes
- No breaking changes (new endpoint)
- Existing clients don't need to use `/handshake` (optional feature)
- Recommended for new client implementations

## References
- Feature request: "could we have a 'handshake' api GET call that echoes the Discovery Settings"
- Related: ADR-0001 (mDNS discovery), ADR-0004 (multi-voice support)
