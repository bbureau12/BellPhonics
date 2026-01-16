from __future__ import annotations

from fastapi import Header, HTTPException
from .config import Settings


def require_api_key(settings: Settings, x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    if not x_api_key or x_api_key.strip() != settings.api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
