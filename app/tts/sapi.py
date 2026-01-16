# app/tts/sapi.py
from __future__ import annotations

import subprocess
from typing import Optional


class WindowsSapiTTS:
    """
    Uses Windows' built-in SAPI via PowerShell.
    Pros: zero Python deps, works offline, good enough quality.
    Cons: Windows-only.
    """

    def speak(self, text: str, *, voice: Optional[str] = None, volume: Optional[float] = None) -> None:
        safe = text.replace('"', '`"')

        # volume: float 0..1 -> SAPI 0..100
        vol = None
        if volume is not None:
            vol = max(0, min(100, int(round(volume * 100))))

        # Optional: pick a voice by name fragment
        # Example: voice="Zira" or "David"
        set_voice = ""
        if voice:
            v = voice.replace('"', '`"')
            set_voice = f'$s.SelectVoice((Get-Culture).TextInfo.ToTitleCase("{v}"));'

        set_volume = ""
        if vol is not None:
            set_volume = f"$s.Volume = {vol};"

        ps = f"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
{set_volume}
{set_voice}
$s.Speak("{safe}")
"""

        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            check=False,
            capture_output=True,
            text=True,
        )
