# ADR 0003: DNS Allowlist with Resolution Caching

**Date:** 2025-01-16

## Status
Accepted

## Context
Bellphonics' `SecurityGate` needs to restrict API access to trusted clients using an allowlist.

Initial implementation supported only IP addresses in the allowlist. However, in local networks with DHCP, clients often have dynamic IPs but stable DNS names (e.g., `echobell.local` via mDNS).

Hardcoding IP addresses is fragile and requires manual updates when DHCP leases change.

## Decision
Support both IP addresses and DNS hostnames in `BELLPHONICS_ALLOWLIST` with DNS resolution caching.

Implementation:
- Parse allowlist entries, detect IPs vs hostnames
- For hostnames: resolve to IP using `socket.gethostbyname()`
- Cache DNS resolutions with 5-minute TTL
- Compare client IP against both direct IP entries and resolved DNS entries

```python
class SecurityGate:
    def __init__(self, allowlist: List[str]):
        self._allowlist = allowlist
        self._dns_cache = {}  # {hostname: (ip, timestamp)}
        self._cache_ttl = 300  # 5 minutes
    
    def _resolve_hostname(self, hostname: str) -> str | None:
        now = time.time()
        
        # Check cache
        if hostname in self._dns_cache:
            ip, timestamp = self._dns_cache[hostname]
            if now - timestamp < self._cache_ttl:
                return ip
        
        # Resolve and cache
        try:
            ip = socket.gethostbyname(hostname)
            self._dns_cache[hostname] = (ip, now)
            return ip
        except socket.gaierror:
            return None
```

## Consequences

### Positive
- ✅ Supports mDNS hostnames (`echobell.local`)
- ✅ Resilient to DHCP IP changes
- ✅ Better UX: configure by semantic name, not IP
- ✅ Caching reduces DNS query overhead
- ✅ Works with `.local` domains via mDNS resolver

### Negative
- ⚠️ DNS resolution can fail (network issues, name not registered)
- ⚠️ Cache adds memory overhead (minimal: ~100 bytes per entry)
- ⚠️ 5-minute TTL means up to 5-minute delay recognizing IP changes

### Neutral
- Backwards compatible: existing IP-only configs still work
- Can mix IPs and hostnames in same allowlist

## Alternatives Considered

### 1. IP-only allowlist, no DNS
Require users to configure IP addresses.

**Rejected because:**
- Fragile in DHCP environments
- Poor UX in mDNS scenarios
- Doesn't align with mDNS discovery feature

### 2. Resolve on every request, no caching
Query DNS for every incoming request.

**Rejected because:**
- Performance overhead (DNS queries can be slow)
- Potential DoS vector (flood with requests → DNS query flood)
- Unnecessary: IPs don't change that frequently

### 3. Longer cache TTL (e.g., 1 hour)
Use longer TTL to reduce DNS queries further.

**Rejected because:**
- Too slow to pick up legitimate IP changes
- 5 minutes balances performance and freshness

### 4. Use reverse DNS on client IP
Resolve client IP to hostname, check against allowlist.

**Rejected because:**
- Not all IPs have reverse DNS records
- Reverse DNS can be spoofed more easily
- Forward resolution (hostname → IP) is more reliable

## Security Considerations
- DNS resolution failures are logged but don't crash the server
- Invalid hostnames in allowlist are skipped (degraded to IP-only)
- Cache prevents DNS query amplification attacks
- Allowlist format validation on startup

## Migration Notes
- Existing IP-only configs: No changes needed
- New hostname configs: Add `.local` or FQDN to `BELLPHONICS_ALLOWLIST`
- Example: `BELLPHONICS_ALLOWLIST=192.168.1.50,echobell.local,127.0.0.1`

## References
- Feature request: "for my securitygate, could I add a dns name allowlist?"
- mDNS/.local domain standard: RFC 6762
