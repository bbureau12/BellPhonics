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
    Piper TTS using the piper-tts Python package with support for multiple voices.
    """

    def __init__(self, *, voices_dir: str, default_voice: str):
        self.voices_dir = Path(voices_dir)
        self.default_voice = default_voice
        self.loaded_voices: dict[str, PiperVoice] = {}
        
        if not self.voices_dir.exists():
            raise RuntimeError(f"Piper voices directory not found: {self.voices_dir}")
        
        # Pre-load the default voice
        self._load_voice(default_voice)
        log.info(f"Piper TTS initialized with default voice: {default_voice}")

    def _load_voice(self, voice_name: str) -> PiperVoice:
        """Load a voice model by name. Caches loaded voices."""
        if voice_name in self.loaded_voices:
            return self.loaded_voices[voice_name]
        
        model_path = self.voices_dir / f"{voice_name}.onnx"
        if not model_path.exists():
            log.warning(f"Voice '{voice_name}' not found at {model_path}, falling back to default")
            if voice_name != self.default_voice:
                return self._load_voice(self.default_voice)
            raise RuntimeError(f"Default voice not found: {model_path}")
        
        voice = PiperVoice.load(model_path)
        self.loaded_voices[voice_name] = voice
        log.info(f"Loaded Piper voice: {voice_name}")
        return voice

    def speak(self, text: str, *, voice: Optional[str] = None, volume: Optional[float] = None) -> None:
        text = (text or "").strip()
        if not text:
            return

        # Use specified voice or fall back to default
        voice_name = voice or self.default_voice
        piper_voice = self._load_voice(voice_name)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name

        try:
            # Synthesize returns an iterable of AudioChunk objects
            # We need to write them to a WAV file
            with wave.open(wav_path, "wb") as wav_file:
                wav_file.setnchannels(1)  # mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(piper_voice.config.sample_rate)
                
                for audio_chunk in piper_voice.synthesize(text):
                    wav_file.writeframes(audio_chunk.audio_int16_bytes)
            
            log.info(f"Synthesized '{text[:50]}...' using voice '{voice_name}'")
            winsound.PlaySound(wav_path, winsound.SND_FILENAME)
        except Exception as e:
            log.exception(f"Error during synthesis: {e}")
        finally:
            try:
                Path(wav_path).unlink()
            except OSError:
                pass
