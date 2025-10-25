# Helios Voice Control - Quick Start

## What You Get

- 🎤 Wake word activation with **"computer"**
- 🗣️ Ask questions naturally
- 🔊 Get **audio responses** on Windows, Linux, and macOS
- 🚫 **No continuous chatting** - single-shot Q&A only

## Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Linux only: Install espeak for TTS
sudo apt-get install espeak espeak-data libespeak-dev

# 3. Add Porcupine key to .env
# Get free key from: https://console.picovoice.ai/
PORCUPINE_API_KEY=your_key_here
```

## Run It

### Terminal 1: Voice Agent API
```bash
python services/voice_agent_api.py
```

### Terminal 2: Voice Listener
```bash
python services/voice_listener.py
```

## Use It

1. **Say:** "computer"
2. **Wait for:** "🎤 Wake word detected!"
3. **Ask:** "What's the status?"
4. **Listen:** Audio response plays automatically

## Example Queries

- "What's the status?"
- "Switch to predictive mode"
- "How much energy have we saved?"
- "Is the system safe?"
- "Compare the performance"

## How It Works

```
Wake Word → Speech to Text → Agent Processing → Text to Speech
(Porcupine)  (Google STT)     (Your Tools)      (pyttsx3)
```

- ✅ **No text input required** - only voice
- ✅ **Audio output on all platforms**
- ✅ **Wake word triggered** - no continuous conversation
- ✅ **Works offline** (except for Google STT)

## That's It!

For detailed setup and troubleshooting, see [docs/VOICE_SETUP.md](docs/VOICE_SETUP.md)
