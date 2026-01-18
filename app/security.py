from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse

log = logging.getLogger("bellphonics.security")


@dataclass
class SecurityConfig:
    api_key: str
    allowlist: set[str]  # IPs or DNS names
    rate_limit_per_min: int = 20
    dedupe_ttl_s: int = 600
    dns_cache_ttl_s: int = 300  # cache DNS lookups for 5 minutes


class SecurityGate:
    def __init__(self, cfg: SecurityConfig):
        self.cfg = cfg
        self._seen_event: dict[str, float] = {}
        self._window_start: float = time.time()
        self._window_count: int = 0
        # Cache DNS lookups: hostname -> (set of IPs, timestamp)
        self._dns_cache: dict[str, tuple[set[str], float]] = {}

    def _resolve_hostname(self, hostname: str) -> set[str]:
        """Resolve a hostname to a set of IP addresses, with caching."""
        now = time.time()
        
        # Check cache
        if hostname in self._dns_cache:
            ips, cached_time = self._dns_cache[hostname]
            if (now - cached_time) < self.cfg.dns_cache_ttl_s:
                return ips
        
        # Resolve DNS
        try:
            # Get all addresses for the hostname
            addr_info = socket.getaddrinfo(hostname, None)
            ips = {info[4][0] for info in addr_info}
            self._dns_cache[hostname] = (ips, now)
            return ips
        except (socket.gaierror, socket.herror):
            # DNS resolution failed, return empty set
            return set()

    def _is_ip_address(self, value: str) -> bool:
        """Check if a string is an IP address (v4 or v6)."""
        try:
            socket.inet_pton(socket.AF_INET, value)
            return True
        except OSError:
            pass
        try:
            socket.inet_pton(socket.AF_INET6, value)
            return True
        except OSError:
            pass
        return False

    def _check_allowlist(self, client_ip: str) -> bool:
        """Check if client IP is in allowlist (supports IPs and DNS names)."""
        if not self.cfg.allowlist:
            return True  # No allowlist means all allowed
        
        for entry in self.cfg.allowlist:
            entry = entry.strip()
            if not entry:
                continue
            
            # Direct IP match
            if entry == client_ip:
                return True
            
            # If entry is not an IP, treat as hostname and resolve
            if not self._is_ip_address(entry):
                resolved_ips = self._resolve_hostname(entry)
                if client_ip in resolved_ips:
                    return True
        
        return False

    def _gc_events(self) -> None:
        now = time.time()
        expired = [eid for eid, ts in self._seen_event.items() if (now - ts) > self.cfg.dedupe_ttl_s]
        for eid in expired:
            self._seen_event.pop(eid, None)

    def check_rate(self) -> bool:
        now = time.time()
        if (now - self._window_start) >= 60:
            self._window_start = now
            self._window_count = 0
        self._window_count += 1
        return self._window_count <= self.cfg.rate_limit_per_min

    def check_event_id(self, event_id: Optional[str]) -> bool:
        if not event_id:
            return True  # let schema enforce required fields
        self._gc_events()
        if event_id in self._seen_event:
            return False
        self._seen_event[event_id] = time.time()
        return True

    def middleware(self, request: Request):
        # allow health and handshake without auth
        if request.url.path in ["/health", "/handshake"]:
            return None

        # allowlist (supports both IPs and DNS names)
        ip = request.client.host if request.client else ""
        log.info(f"Checking allowlist for IP: {ip}, allowlist: {self.cfg.allowlist}")
        if not self._check_allowlist(ip):
            log.warning(f"IP {ip} not in allowlist - returning 403")
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})

        # api key (case-insensitive header lookup)
        key = request.headers.get("x-api-key", "")
        if not key or key.strip() != self.cfg.api_key:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        # rate limit
        if not self.check_rate():
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

        return None
