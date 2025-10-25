# Helios Voice Control Setup - Cross-Platform Edition

## Overview

The Helios voice control system uses:
1. **Porcupine** wake word detection ("computer")
2. **Google Speech Recognition** for transcribing your questions
3. **Helios Agent** for processing queries and controlling the system
4. **pyttsx3** for cross-platform audio responses (Windows/Linux/macOS)

## Architecture

```
You say "computer" → Porcupine detects wake word
                   ↓
You ask question → Google STT transcribes
                   ↓
Text query → Voice Agent API processes with Helios tools
                   ↓
Response text → pyttsx3 TTS plays audio response (all platforms!)
```

## Setup Instructions

### 1. Install Dependencies

```bash
# Install all voice requirements
pip install -r requirements.txt

# This includes:
# - SpeechRecognition (for STT)
# - pvporcupine (wake word detection)
# - pvrecorder (audio recording)
# - pyttsx3 (cross-platform TTS)
```

### Platform-Specific TTS Setup

#### Linux
```bash
# Install espeak for TTS
sudo apt-get install espeak espeak-data libespeak-dev

# Or use Festival (alternative)
sudo apt-get install festival
```

#### Windows
No additional setup needed - uses built-in Windows SAPI.

#### macOS
No additional setup needed - uses built-in NSSpeechSynthesizer.

### 2. Get Porcupine API Key

1. Go to https://console.picovoice.ai/
2. Create a free account
3. Copy your Access Key
4. Add to your `.env`:
   ```
   PORCUPINE_API_KEY=your_key_here
   ```

### 3. Verify Configuration

```bash
python config/config.py
```

Should show:
```
Porcupine Key: Configured [OK]
```

## Running the System

You need to run TWO services:

### Terminal 1: Voice Agent API

```bash
python services/voice_agent_api.py
```

### Terminal 2: Voice Listener

```bash
python services/voice_listener.py
```

## Usage

1. Say: **"computer"**
2. Wait for: `🎤 Wake word detected!`
3. Ask your question
4. Listen to the audio response

## Available Commands

- "What's the status?"
- "Switch to predictive mode"
- "How much energy have we saved?"
- "Is the system safe?"
- "Compare the performance"

## Troubleshooting

### Linux: "TTS initialization failed"
```bash
sudo apt-get install espeak espeak-data libespeak-dev
```

### "Could not understand audio"
- Speak clearly after wake word
- Check microphone permissions

### "No Porcupine API key"
Add `PORCUPINE_API_KEY` to `.env` file

## Configuration

### Change Wake Word
Edit `voice_listener.py` line 47:
```python
keywords=['jarvis']  # or 'alexa', 'hey google', etc.
```

### Adjust TTS Speed
Edit `voice_agent_api.py` line 46:
```python
tts_engine.setProperty('rate', 175)  # Lower = slower
```
