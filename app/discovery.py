from __future__ import annotations

import asyncio
import logging
import socket
from dataclasses import dataclass, field
from typing import Optional

from zeroconf import IPVersion, ServiceInfo, Zeroconf
from zeroconf.asyncio import AsyncZeroconf

log = logging.getLogger("bellphonics.discovery")


@dataclass(frozen=True)
class DiscoveryConfig:
    enabled: bool
    service_type: str = "_bellphonics._tcp.local."
    instance_name: str = "Bellphonics"
    port: int = 8099
    host: str = ""  # if empty, infer local hostname
    zone: str = ""  # optional zone metadata
    subzone: str = ""  # optional subzone metadata
    txt: dict[str, str] = field(default_factory=dict)  # metadata


class MdnsAdvertiser:
    def __init__(self, cfg: DiscoveryConfig):
        self.cfg = cfg
        self.aiozc: Optional[AsyncZeroconf] = None
        self.info: Optional[ServiceInfo] = None

    async def start(self) -> None:
        if not self.cfg.enabled:
            log.info("mDNS discovery disabled")
            return

        hostname = (self.cfg.host.strip() or socket.gethostname()).rstrip(".")
        # mDNS hostnames should end with .local
        if not hostname.lower().endswith(".local"):
            hostname = f"{hostname}.local"

        instance = self.cfg.instance_name.strip() or "Bellphonics"
        fullname = f"{instance}.{self.cfg.service_type}"

        # Best-effort local IP (works for typical home LAN)
        ip = socket.gethostbyname(socket.gethostname())
        addresses = [socket.inet_aton(ip)]

        # Build properties from config txt, adding zone/subzone if provided
        props = {k.encode("utf-8"): v.encode("utf-8") for k, v in (self.cfg.txt or {}).items()}
        if self.cfg.zone:
            props[b"zone"] = self.cfg.zone.encode("utf-8")
        if self.cfg.subzone:
            props[b"subzone"] = self.cfg.subzone.encode("utf-8")

        self.aiozc = AsyncZeroconf(ip_version=IPVersion.V4Only)
        self.info = ServiceInfo(
            type_=self.cfg.service_type,
            name=fullname,
            addresses=addresses,
            port=self.cfg.port,
            properties=props,
            server=hostname,
        )
        await self.aiozc.async_register_service(self.info)
        log.info(f"mDNS service registered: {fullname} at {ip}:{self.cfg.port}")

    async def stop(self) -> None:
        if self.aiozc and self.info:
            try:
                await self.aiozc.async_unregister_service(self.info)
                log.info("mDNS service unregistered")
            finally:
                await self.aiozc.async_close()
        self.aiozc = None
        self.info = None
