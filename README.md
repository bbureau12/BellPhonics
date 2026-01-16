# Bellphonics

**Bellphonics** is a calm, policy-driven audio annunciation service designed to give physical voice to events detected by **EchoBell**.

Bellphonics does not decide *what matters*.
It does not watch cameras, classify intent, or infer meaning.

Bellphonics speaks **only when asked** — and only what it is told to say.

---

## Purpose

Bellphonics exists to solve a very specific problem:

> *How should a home or space speak — clearly, calmly, and without panic — when something meaningful happens?*

It is built to:
- Convert **explicit speech events** into audible announcements
- Play audio through **locally attached or remote speakers**
- Enforce **cooldowns and deduplication** so speech never becomes noise
- Remain **hardware-agnostic** and **engine-agnostic**

Bellphonics is intentionally conservative. Silence is preferred to chatter.

---

## Design Philosophy

Bellphonics follows a few strict principles:

### 1. Policy lives elsewhere
Bellphonics never decides *if* something should be spoken.

That decision belongs upstream (typically in EchoBell’s policy layer).

Bellphonics only answers:
> “Given this request, how do I speak it safely and reliably?”

---

### 2. Speech should be calm, brief, and intentional
Bellphonics is not an alarm system.
It is an annunciator.

Messages should be:
- Short
- Neutral
- Non-escalating

Examples:
- “Delivery at the front door.”
- “Someone is at the side entrance.”
- “Attention. Unknown visitor lingering.”

---

### 3. Deduplication is mandatory
Repeated speech is worse than silence.

Bellphonics enforces cooldowns and replay protection even if the publisher retries or restarts.

---

### 4. Hardware is replaceable
Speakers fail. Devices change. Rooms evolve.

Bellphonics treats audio output as an implementation detail.

---

## What Bellphonics Is

- A **standalone service** (typically running on a device connected to speakers)
- A **subscriber** to speech events (HTTP today, pub/sub later)
- A **TTS + playback orchestrator**

---

## What Bellphonics Is *Not*

Bellphonics does **not**:
- Perform computer vision
- Classify intent or threat
- Decide who should be notified
- Record audio
- Monitor microphones
- Phone emergency services

Those concerns belong elsewhere.

---

## Architecture Overview

```
EchoBell (policy)
   |
   |  SpeechEvent
   v
Bellphonics
   |
   |  TTS + Playback
   v
Speakers
```

Bellphonics is designed to be the **last step** in a chain of reasoning — never the first.

---

## Setup

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -e .
   ```
4. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
5. Edit `.env` and set your `BELLPHONICS_API_KEY`

### Voice Models (Piper TTS)

If using Piper TTS (recommended for offline, high-quality speech):

1. Download a Piper voice model from [rhasspy/piper releases](https://github.com/rhasspy/piper/releases)
2. Create the voicepacks directory:
   ```bash
   mkdir -p app/tts/voicepacks
   ```
3. Place both the `.onnx` and `.onnx.json` files in `app/tts/voicepacks/`
4. Update `.env` to configure Piper:
   ```bash
   BELLPHONICS_TTS_BACKEND=piper
   BELLPHONICS_PIPER_MODEL=app/tts/voicepacks/your-model-name.onnx
   ```

**Recommended voices:**
- `en_GB-alba-medium` - British English, clear quality
- `en_US-lessac-medium` - American English, natural quality

Voice models are not included in the repository due to their size (100-200MB each).

### Running

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8099
```

Or use the VS Code debugger (F5) with the included launch configuration.

---

## Speech Event Contract

Bellphonics consumes explicit, structured speech requests.

```json
{
  "event_id": "uuid",
  "ts": 1768434103,
  "text": "Delivery at the front door.",
  "severity": "info",
  "room": "kitchen",
  "cooldown_key": "speak:front:delivery",
  "cooldown_s": 25,
  "voice": "en_US",
  "volume": 0.8
}
```

### Field notes
- `event_id` prevents replay
- `cooldown_key` ensures deduplication
- `room` allows future multi-speaker routing
- `severity` may influence voice or volume (never content)

Bellphonics does not invent speech. It only renders it.

---

## Transport

### Current
- **HTTP (FastAPI)** — simple, explicit, debuggable

### Planned
- **MQTT** for pub/sub environments
- Multiple concurrent subscribers

The event schema is designed to remain stable across transports.

---

## TTS Engines

Bellphonics supports pluggable TTS engines.

Initial targets:
- **Piper** (offline, high quality, preferred)
- OS-native engines (macOS `say`, Windows SAPI)
- Mock engine for testing

The engine choice is an implementation detail, not a contract.

---

## Audio Output

Bellphonics supports:
- Hardwired speakers
- USB audio devices
- External DACs
- Any system-supported playback device

Audio playback is serialized to prevent overlap.

---

## Security Model

Bellphonics assumes a **trusted local network** but still enforces:
- API key authentication
- Explicit allowlists
- No unsolicited outbound communication

If Bellphonics cannot authenticate a request, it stays silent.

---

## Typical Deployment

- Raspberry Pi or mini PC
- Connected to an amplifier or powered speakers
- Runs continuously as a small system service

Bellphonics is designed to survive restarts without repeating speech.

---

## Relationship to EchoBell

EchoBell and Bellphonics are separate projects by design.

- EchoBell observes and reasons
- Bellphonics speaks

They communicate only through a narrow, explicit contract.

This separation keeps both systems understandable and safe.

---

## Non-Goals

Bellphonics will never:
- Try to sound human
- Engage in conversation
- React emotionally
- Make decisions about urgency

Bellphonics exists to be *clear*, not clever.

---

## Status

Bellphonics is in early development.

The first milestone is:
- Accept a speech event
- Enforce cooldowns
- Speak reliably through a single output device

Everything else is incremental.

---

## License

TBD

---

> *Bellphonics — when the house speaks, it should speak calmly.*

