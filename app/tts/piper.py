from __future__ import annotations

import logging
from typing import Optional
from pathlib import Path
import tempfile
import winsound
import wave

from piper import PiperVoice

log = logging.getLogger("bellphonics.tts.piper")


class PiperTTS:
    """
    Piper TTS using the piper-tts Python package.
    """

    def __init__(self, *, model_path: str):
        model = Path(model_path)
        if not model.exists():
            raise RuntimeError(f"Piper model not found: {model}")

        self.voice = PiperVoice.load(model)
        log.info(f"Loaded Piper voice from {model}")

    def speak(self, text: str, *, voice: Optional[str] = None, volume: Optional[float] = None) -> None:
        text = (text or "").strip()
        if not text:
            return

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name

        try:
            # Synthesize returns an iterable of AudioChunk objects
            # We need to write them to a WAV file
            with wave.open(wav_path, "wb") as wav_file:
                wav_file.setnchannels(1)  # mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.voice.config.sample_rate)
                
                for audio_chunk in self.voice.synthesize(text):
                    wav_file.writeframes(audio_chunk.audio_int16_bytes)
            
            log.info(f"Synthesized audio to {wav_path}")
            winsound.PlaySound(wav_path, winsound.SND_FILENAME)
        except Exception as e:
            log.exception(f"Error during synthesis: {e}")
        finally:
            try:
                Path(wav_path).unlink()
            except OSError:
                pass
