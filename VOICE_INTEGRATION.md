# Gemini Voice Chat Integration - Helios Dashboard

The Gemini Live API voice chat is now **fully integrated** into your existing Helios dashboard! No separate server needed.

## What's Integrated

✅ **Unified Backend** - Voice chat runs on the same Flask server as your dashboard (port 5000)
✅ **Dashboard UI** - Voice controls added to the "Voice Assistant" panel (bottom-right)
✅ **Single Command** - Run everything with one command
✅ **Shared WebSocket** - Uses `flask-sock` alongside your existing `flask-socketio`

## Quick Start

### 1. Install New Dependencies

```bash
# Activate virtual environment first!
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install requirements
pip install -r requirements.txt
```

New packages added:
- `flask-sock` - WebSocket support for voice chat
- `websockets` - Async WebSocket client for Gemini
- `certifi` - SSL certificate verification
- `flask-cors` - CORS support

### 2. Configure Gemini API Key

Edit your `.env` file:

```env
# Add this line
GEMINI_API_KEY=your_actual_api_key_here

# Get your key at: https://aistudio.google.com/app/apikey
```

### 3. Run the Dashboard

```bash
# From the project root
cd dashboard
python dashboard.py
```

Visit: **http://localhost:5000**

## How to Use

1. **Open Dashboard** - Navigate to http://localhost:5000
2. **Find Voice Assistant Panel** - Bottom-right panel with voice controls
3. **Click "Start Voice Chat"** - Grants microphone permission and connects
4. **Talk Naturally** - Helios AI will respond via audio
5. **Click "Stop Chat"** - Ends the conversation

### Keyboard Shortcut

Press `Ctrl + Space` to toggle voice chat on/off!

## What Changed

### Backend (`dashboard/dashboard.py`)

Added at line 66-90:
```python
# Gemini Voice Chat Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
GEMINI_MODEL = "models/gemini-2.5-flash-exp-native-audio-thinking-dialog"
HELIOS_VOICE_INSTRUCTION = {
    "parts": [{
        "text": """You are Helios, an AI assistant integrated into a solar panel tracking dashboard..."""
    }]
}
```

Added at line 424-658:
- `GeminiVoiceConnection` class - Manages WebSocket connection to Gemini
- `@sock.route('/ws/gemini-voice')` - WebSocket endpoint for voice chat

### Frontend

**HTML Changes** (`dashboard/templates/index.html`):
- Updated "Voice Command Log" panel to "Voice Assistant" (line 238-266)
- Added Start/Stop voice chat buttons
- Added voice status indicator
- Included `audio-streamer.js` and `gemini-voice.js` scripts

**New JavaScript** (`dashboard/static/js/components/gemini-voice.js`):
- `GeminiVoiceChat` class integrates with dashboard
- Handles button clicks and status updates
- Logs voice events to the voice log panel

**New CSS** (`dashboard/static/css/main.css`):
- Voice control button styles (line 979-1153)
- Status indicators with animations
- Responsive layout adjustments

## Features

### AI Personality

Helios is configured to:
- Specialize in solar energy and renewable systems
- Understand dashboard metrics (power, energy, cloud coverage, etc.)
- Keep responses brief and conversational (2-3 sentences)
- Ask one question at a time

### Audio Processing

- **Input**: Browser microphone → 16kHz PCM → Gemini
- **Output**: Gemini 24kHz PCM → Browser playback
- **Quality**: Echo cancellation, noise suppression, auto-gain
- **Playback**: Sequential queue prevents choppy audio

### Status Indicators

- **Disconnected** (gray) - Ready to start
- **Connecting** (yellow) - Establishing connection
- **Connected** (green) - Active chat session
- **Speaking** (cyan pulsing) - User is talking
- **Error** (red) - Connection problem

## Architecture

```
Dashboard UI (localhost:5000)
    ↓
Voice Assistant Panel
    ↓
WebSocket: /ws/gemini-voice
    ↓
dashboard.py (Flask + flask-sock)
    ↓
Gemini Live API (wss://generativelanguage.googleapis.com/...)
```

## Customization

### Change AI Personality

Edit `HELIOS_VOICE_INSTRUCTION` in [dashboard/dashboard.py](dashboard/dashboard.py:71-90):

```python
HELIOS_VOICE_INSTRUCTION = {
    "parts": [{
        "text": """Your custom system instruction here..."""
    }]
}
```

### Change Voice

Edit line 467 in [dashboard/dashboard.py](dashboard/dashboard.py:467):

```python
"voice_name": "Puck"  # Options: Puck, Charon, Kore, Fenrir, Aoede
```

### Adjust Button Styles

Edit [dashboard/static/css/main.css](dashboard/static/css/main.css:979-1153) in the "GEMINI VOICE CHAT STYLES" section.

## Troubleshooting

### "GEMINI_API_KEY not configured"

**Cause**: Environment variable not set
**Fix**: Add `GEMINI_API_KEY=your_key_here` to `.env` file and restart server

### Voice chat button doesn't appear

**Cause**: JavaScript not loading
**Fix**: Check browser console for errors. Verify files exist:
- `dashboard/static/js/audio-streamer.js`
- `dashboard/static/js/components/gemini-voice.js`

### Microphone permission denied

**Cause**: Browser requires user permission
**Fix**: Click "Allow" when prompted. For HTTPS requirement, localhost is exempt.

### Audio is garbled or wrong speed

**Cause**: Incorrect sample rate
**Fix**: Verify line 523 in dashboard.py has `"mime_type": "audio/pcm;rate=16000"`

### Dependencies won't install

**Cause**: Version conflicts or externally-managed environment
**Fix**: Use virtual environment:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Testing

### Verify Installation

```bash
# Check if Gemini is configured
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✅ Gemini configured' if os.getenv('GEMINI_API_KEY') else '❌ Not configured')"

# Check dependencies
python -c "import flask_sock, websockets, certifi; print('✅ Dependencies OK')"
```

### Test Voice Chat

1. Start dashboard: `python dashboard.py`
2. Check terminal output:
   ```
   Gemini Voice Chat: Enabled
   ```
3. Open browser: http://localhost:5000
4. Click "Start Voice Chat"
5. Check browser console for connection logs
6. Speak and verify Gemini responds

## File Structure

```
helios/
├── dashboard/
│   ├── dashboard.py              # ← Gemini integration added here
│   ├── templates/
│   │   └── index.html           # ← Voice controls added here
│   └── static/
│       ├── js/
│       │   ├── audio-streamer.js         # ← New: Audio processing
│       │   └── components/
│       │       └── gemini-voice.js       # ← New: Voice chat component
│       └── css/
│           └── main.css          # ← Voice styles added here
├── requirements.txt              # ← Updated with new dependencies
├── .env.example                  # ← Updated with GEMINI_API_KEY
└── VOICE_INTEGRATION.md          # ← This file
```

## Standalone Voice Chat (Optional)

The standalone voice chat app (`voice_chat.py`) is still available if you want to run it separately:

```bash
cd dashboard
python voice_chat.py  # Runs on port 5001
```

Visit: http://localhost:5001/voice

## API Endpoints

### HTTP Routes

- `GET /` - Main dashboard (includes voice chat)
- `GET /health` - Health check

### WebSocket Routes

- `ws://localhost:5000/socket.io/...` - SocketIO (dashboard data)
- `ws://localhost:5000/ws/gemini-voice` - Voice chat (Gemini)

## Performance Notes

- Voice chat runs in separate threads (non-blocking)
- Minimal impact on dashboard performance
- Audio streaming uses efficient binary WebSocket transport
- Sequential audio playback prevents buffer overflow

## Security Notes

- SSL verification enabled via `certifi`
- CORS restricted via `ALLOWED_ORIGINS` environment variable
- API key never exposed to frontend
- Microphone permission required from user

## Browser Compatibility

- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari (macOS/iOS)
- ❌ IE11 (Web Audio API not supported)

Requires:
- Web Audio API
- WebSocket support
- `getUserMedia` API

## Next Steps

1. **Test thoroughly** - Try various questions about solar energy
2. **Customize personality** - Edit system instruction to match your needs
3. **Monitor logs** - Check terminal for connection/error messages
4. **Share feedback** - Report issues or suggestions

## Resources

- [Gemini Live API Docs](https://ai.google.dev/api/multimodal-live)
- [Get API Key](https://aistudio.google.com/app/apikey)
- [Flask-Sock Docs](https://flask-sock.readthedocs.io/)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)

---

**Congratulations!** 🎉 Your dashboard now has integrated voice chat with Gemini AI!

Need help? Check the troubleshooting section or review the code comments in the integration files.
