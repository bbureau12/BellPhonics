# ADR 0004: Multi-Voice Architecture with Directory-Based Loading

**Date:** 2025-01-16

## Status
Accepted

## Context
Bellphonics uses Piper TTS for neural text-to-speech. Users want to select different voices for different announcements (e.g., British voice for doorbell, American voice for alerts).

Initial implementation loaded a single ONNX model from a hardcoded path. Supporting multiple voices required rethinking the voice loading architecture.

## Decision
Use a directory-based voice loading system with on-demand caching.

**Configuration:**
- `BELLPHONICS_PIPER_VOICES_DIR`: Directory containing `.onnx` voice files
- `BELLPHONICS_PIPER_DEFAULT_VOICE`: Default voice name (without `.onnx` extension)

**Implementation:**
```python
class PiperTTS:
    def __init__(self, voices_dir: Path, default_voice: str):
        self._voices_dir = voices_dir
        self._default_voice = default_voice
        self._voice_cache = {}  # Cache loaded PiperVoice objects
    
    def _load_voice(self, voice_name: str) -> PiperVoice:
        if voice_name in self._voice_cache:
            return self._voice_cache[voice_name]
        
        model_path = self._voices_dir / f"{voice_name}.onnx"
        voice = PiperVoice.load(str(model_path))
        self._voice_cache[voice_name] = voice
        return voice
    
    def speak(self, text: str, voice: str | None = None):
        voice_name = voice or self._default_voice
        piper_voice = self._load_voice(voice_name)
        # ... synthesize
```

**Voice Discovery:**
- `/handshake` endpoint scans `voices_dir` for `.onnx` files
- Returns list of available voice names
- Clients can query capabilities before making requests

## Consequences

### Positive
- ✅ Unlimited voice support (just drop `.onnx` files in directory)
- ✅ On-demand loading: only load voices that are used
- ✅ Caching prevents repeated model loading
- ✅ Client-driven voice selection via API
- ✅ Easy to add new voices without code changes

### Negative
- ⚠️ Memory usage grows with number of loaded voices
- ⚠️ First use of a voice has loading overhead (~1-2s)
- ⚠️ No validation that voice exists until first use (mitigated: `/handshake` pre-lists)

### Neutral
- Requires organizing voice files in directory structure
- `.onnx.json` config files must be co-located with `.onnx` models

## Alternatives Considered

### 1. Single model path (original design)
Load one voice model at startup.

**Rejected because:**
- No voice variety
- Can't change voice without restart
- Poor UX for multi-zone deployments

### 2. Pre-load all voices at startup
Load all `.onnx` files in directory during app initialization.

**Rejected because:**
- High memory usage (each model ~20-50 MB)
- Slow startup time
- Wasteful if some voices never used

### 3. Voice manifest file (JSON list)
Require `voices.json` manifest listing available voices.

**Rejected because:**
- Extra configuration burden
- Directory scanning is simple and reliable
- Manifest can get out of sync with actual files

### 4. Download voices on-demand from remote server
Fetch voice models from network when requested.

**Rejected because:**
- Adds network dependency
- Security concerns (untrusted model sources)
- Slow first use
- Overcomplicated for local TTS service

## Voice Model Organization
Expected directory structure:
```
app/tts/voicepacks/
├── en_GB-alba-medium.onnx
├── en_GB-alba-medium.onnx.json
├── en_GB-jenny_dioco-medium.onnx
├── en_GB-jenny_dioco-medium.onnx.json
├── en_US-lessac-medium.onnx
└── en_US-lessac-medium.onnx.json
```

Voice names: Filename without `.onnx` extension (e.g., `en_GB-alba-medium`)

## Performance Characteristics
- Voice loading: ~1-2 seconds (ONNX model initialization)
- Synthesis after loading: ~100-500ms for typical announcement
- Memory per voice: ~20-50 MB (model weights)
- Cache hit rate: High in practice (few voices, repeated use)

## Migration Notes
- Old config: `BELLPHONICS_PIPER_MODEL_PATH=/path/to/model.onnx`
- New config:
  ```bash
  BELLPHONICS_PIPER_VOICES_DIR=app/tts/voicepacks
  BELLPHONICS_PIPER_DEFAULT_VOICE=en_GB-alba-medium
  ```
- Move existing `.onnx` and `.onnx.json` files to `voicepacks/` directory

## References
- Feature request: "could we allow the user to select a voice if piper is chosen"
- Piper voice downloads: https://github.com/rhasspy/piper/releases
