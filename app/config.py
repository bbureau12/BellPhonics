from __future__ import annotations

from dataclasses import dataclass
import os


def _env(key: str, default: str | None = None) -> str | None:
    v = os.getenv(key)
    if v is None:
        return default
    v = v.strip()
    return v if v else default


@dataclass(frozen=True)
class Settings:
    api_key: str
    bind_host: str = "0.0.0.0"
    bind_port: int = 8099

    default_cooldown_s: int = 20
    dedupe_ttl_s: int = 300

    tts_backend: str = "mock"


def load_settings() -> Settings:
    api_key = _env("BELLPHONICS_API_KEY", "") or ""
    if not api_key:
        # Fail closed: service should not accept unauthenticated speech.
        raise RuntimeError("BELLPHONICS_API_KEY must be set")

    return Settings(
        api_key=api_key,
        bind_host=_env("BELLPHONICS_BIND_HOST", "0.0.0.0") or "0.0.0.0",
        bind_port=int(_env("BELLPHONICS_BIND_PORT", "8099") or "8099"),
        default_cooldown_s=int(_env("BELLPHONICS_DEFAULT_COOLDOWN_S", "20") or "20"),
        dedupe_ttl_s=int(_env("BELLPHONICS_DEDUPE_TTL_S", "300") or "300"),
        tts_backend=(_env("BELLPHONICS_TTS_BACKEND", "mock") or "mock").lower(),
    )
