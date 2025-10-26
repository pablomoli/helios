# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Helios AI is a voice-controlled solar tracking system with real-time Arduino hardware integration. The system uses a **single-service architecture** where the dashboard (port 5000) handles all functionality including voice control, WebSocket communication, and UI.

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Linux only: TTS support
sudo apt-get install espeak espeak-data libespeak-dev

# Test configuration
python config/config.py
```

### Required API Keys (.env file)

```bash
GOOGLE_GENAI_API_KEY=your_key_here      # Gemini API from ai.google.dev
OPENWEATHER_API_KEY=your_key_here        # Free from openweathermap.org
WEBSOCKET_SERVER_URL=ws://localhost:5000
DASHBOARD_PORT=5000
```

**Security:** Never commit `.env` file. It's in `.gitignore`.

## Running the System

**Single Command Start:**

```bash
./start_helios.sh
```

This starts the dashboard on http://localhost:5000 - everything runs in one service!

**To Stop:**

```bash
./stop_helios.sh
```

## Architecture: Single-Service Model (Option A)

**Critical Concept:** Everything runs through the dashboard on port 5000. No separate services needed.

```
┌─────────────────────────────────────────────────┐
│     Dashboard (Port 5000) - ALL-IN-ONE          │
│     • Flask web server                          │
│     • WebSocket hub (SocketIO)                  │
│     • Browser-based voice control (Web Audio)   │
│     • Gemini 2.5 Flash Native Audio Dialog      │
│     • Real-time Arduino data visualization      │
│     • Command routing to Arduino                │
└─────────────────────────────────────────────────┘
           │
           ▼
    Arduino (USB Serial)
```

### WebSocket Events

**From Arduino (via dashboard):**
- `sensors_raw` - LDR sensors, voltage, current, power (every 1-2s)
- `status` - Mode, pan/tilt angles, sun position
- `impact` - Energy saved (kWh)
- `safety` - Safety alerts, servo health, temperature
- `ai_performance_delta` - A/B comparison data

**To Arduino (via dashboard):**
- `command_position` - Move servos: `{"pan_angle_deg": 90, "tilt_angle_deg": 45}`
- `command_mode` - Switch mode: `{"mode": "Predictive"}` or `{"mode": "Reactive"}`

**Voice Control Events:**
- `voice_log` - Voice queries and responses logged to dashboard

**Important:** WebSocket events use centralized constants from `config.config.Events` class.

## Voice Control System

Voice control uses **browser-based Web Audio API** with Gemini 2.5 Flash Native Audio Dialog integration.

### Components

1. **dashboard/static/js/components/gemini-voice.js** - Browser microphone capture + audio processing
2. **dashboard/voice_handler.py** - Backend Gemini integration with wake word detection
3. **dashboard/static/js/components/ai-voice-interface.js** - Spectrogram visualization

### Voice Flow

```
Click 🎤 button → Browser captures audio → Web Audio API processes
                                                    ↓
                                    Send audio to /api/voice-query
                                                    ↓
                        voice_handler.py detects "Helios" wake word
                                                    ↓
                            Gemini 2.5 processes query with system context
                                                    ↓
                        Response sent back to browser + spoken via Web Speech API
                                                    ↓
                            Spectrogram visualizes audio in real-time
```

### Gemini Integration

The voice handler in `dashboard/voice_handler.py` integrates with Gemini:

**System Context** (automatically provided):
- Current sensor data (power, voltage, LDR values)
- System status (mode, pan/tilt angles)
- Safety status
- Impact metrics (energy saved)

**Wake Word Detection:**
- Listens for "Helios" at the start of user input
- Only responds when wake word is detected

**Response Generation:**
- Uses Gemini 2.5 Flash Native Audio Dialog model
- Processes audio directly (native audio support)
- Returns natural language responses based on system state

## Arduino Communication Protocol

Arduino communicates via USB serial (9600 baud) using JSON messages with `\n` terminator.

**Arduino → Computer:**
```json
{"type": "sensors", "timestamp": 123, "ldr_tl": 812, "panel_power_mW": 728.47}
{"type": "status", "mode": "Predictive", "pan_angle_deg": 90.0}
{"type": "energy", "energy_saved_kWh": 0.0012}
```

**Computer → Arduino:**
```json
{"type": "position", "pan_angle_deg": 95.0, "tilt_angle_deg": 40.0}
{"type": "mode", "mode": "Predictive"}
```

The `type` field determines how dashboard routes the data to WebSocket events.

## Configuration System

All services use `config.config.Config` for centralized configuration:

```python
from config.config import Config, Events

# Access config
Config.WEBSOCKET_SERVER_URL  # ws://localhost:5000
Config.GOOGLE_GENAI_API_KEY  # Never log this!

# Use event constants
socketio.emit(Events.COMMAND_MODE, {"mode": "Predictive"})

@socketio.on(Events.SENSORS_RAW)
def on_sensors(data):
    # Process sensor data
    pass
```

**Safe config display:**
```python
print(Config.get_safe_config_string())  # Hides secrets
```

## Key Design Patterns

### Pattern 1: Browser-Based Voice Control

Voice control runs entirely in the browser using Web Audio API:

```javascript
class GeminiVoice {
    async startListening() {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {echoCancellation: true, noiseSuppression: true}
        });

        this.audioContext = new AudioContext();
        this.analyser = this.audioContext.createAnalyser();
        this.microphone = this.audioContext.createMediaStreamSource(stream);
        this.microphone.connect(this.analyser);

        // Connect to spectrogram visualization
        window.aiVoiceInterface.startRealAudio(this.analyser);

        // Record audio and send to backend
        this.mediaRecorder = new MediaRecorder(stream);
        this.mediaRecorder.start();
    }

    async processAudio(audioBlob) {
        const base64Audio = await this.blobToBase64(audioBlob);
        const response = await fetch('/api/voice-query', {
            method: 'POST',
            body: JSON.stringify({
                audio: base64Audio,
                system_data: this.getSystemData()
            })
        });

        const result = await response.json();
        if (result.wake_word_detected && result.response_text) {
            this.speak(result.response_text);
        }
    }
}
```

### Pattern 2: Backend Voice Processing

Voice handler processes audio with Gemini and system context:

```python
def process_voice_query(audio_data, wake_word_detected=False):
    """Process voice query using Gemini"""
    if not wake_word_detected:
        return {'success': False, 'message': 'Wake word "Helios" not detected'}

    # Get current system context
    context = get_system_context()

    # Send to Gemini with audio and context
    # (Currently simplified for testing - see voice_handler.py)

    return {
        'success': True,
        'response_text': response,
        'should_respond': True
    }

def simple_wake_word_detection(audio_data):
    """Detect 'Helios' wake word in audio"""
    # Currently bypassed for testing (always returns True)
    # TODO: Implement actual wake word detection
    return True
```

### Pattern 3: Dashboard API Endpoints

Dashboard provides REST endpoints for voice control:

```python
@app.route('/api/gemini-config')
def get_gemini_config():
    """Provide Gemini API configuration"""
    return {'api_key': Config.GOOGLE_GENAI_API_KEY}

@app.route('/api/voice-query', methods=['POST'])
def handle_voice_query_api():
    """Handle voice query from browser"""
    data = request.json
    audio_data = data.get('audio')
    system_data = data.get('system_data', {})

    # Update system context
    update_system_data('sensors', system_data.get('sensors'))

    # Process with wake word detection
    wake_word_detected = simple_wake_word_detection(audio_data)

    if wake_word_detected:
        result = process_voice_query(audio_data, wake_word_detected=True)
        return jsonify({
            'wake_word_detected': True,
            'response_text': result.get('response_text', ''),
            'success': result.get('success', False)
        })
    else:
        return jsonify({'wake_word_detected': False})
```

## Testing

```bash
# Test config loading
python config/config.py

# Test dashboard startup
./start_helios.sh

# Check dashboard logs
tail -f /tmp/helios_dashboard.log

# Test TTS in browser (open browser console on dashboard)
window.geminiVoice.speak('Test message')
```

## Common Development Tasks

### Adding a New WebSocket Event

1. Add event constant to `config/config.py` in `Events` class
2. Update Arduino to send new JSON message type (if applicable)
3. Update dashboard to handle the event
4. Update frontend JavaScript to display the data

### Adding a New Voice Command Capability

1. Update system context in `dashboard/voice_handler.py` `get_system_context()`
2. Ensure Gemini has access to the data needed to answer queries
3. Test by clicking mic button and saying "Helios, [your query]"

### Debugging Voice Control

```javascript
// In browser console:
console.log(window.geminiVoice); // Check voice control state
console.log(window.aiVoiceInterface); // Check spectrogram state

// Test microphone:
navigator.mediaDevices.getUserMedia({audio: true})
    .then(stream => console.log('Mic access OK'))
    .catch(err => console.error('Mic error:', err));
```

### Debugging WebSocket Communication

```python
# In dashboard.py, add verbose logging:
@socketio.on('*')
def catch_all(event, data):
    print(f"SocketIO Event: {event}, Data: {data}")
```

## Important Constraints

1. **Single Service Architecture:** Everything runs through dashboard on port 5000 - no separate services
2. **Security:** Never commit `.env` file or log API keys
3. **Arduino safety:** Always validate servo angles (0-180°) before sending commands
4. **Voice responses:** Keep responses concise (1-3 sentences) for clarity
5. **Browser compatibility:** Web Audio API requires HTTPS or localhost
6. **Wake word:** System only responds when "Helios" is detected at start of input

## Project Structure

```
helios/
├── adk/
│   └── helios_agent/
│       └── agent.py              # Legacy ADK agent (not used in Option A)
├── config/
│   ├── __init__.py               # Exports Config and Events
│   └── config.py                 # Centralized config + Events
├── dashboard/
│   ├── dashboard.py              # Main Flask app (ALL-IN-ONE SERVICE)
│   ├── voice_handler.py          # Gemini voice integration
│   ├── templates/
│   │   └── index.html            # Main dashboard UI
│   └── static/
│       ├── css/
│       │   └── main.css          # Dashboard styles
│       └── js/
│           └── components/
│               ├── gemini-voice.js          # Browser voice control
│               └── ai-voice-interface.js    # Spectrogram visualization
├── docs/
│   ├── SYSTEM_ARCHITECTURE.md    # Detailed architecture
│   ├── ARDUINO_PROTOCOL.md       # Serial protocol spec
│   ├── VOICE_SETUP.md           # Voice system setup
│   └── AGENT_DATAFLOW.md        # Agent ↔ Arduino integration
├── services/
│   └── (legacy services - not used in Option A)
├── .env                          # Secrets (never commit!)
├── requirements.txt              # Python dependencies
├── start_helios.sh              # Quick start script
└── stop_helios.sh               # Stop script
```

## Dashboard Layout

The dashboard uses a 12-column × 3-row CSS grid layout:

```
Row 1: Sky Map (cols 1-6)        | Analytics (cols 7-12)
Row 2: Performance Graph (cols 1-8) | Impact Metrics (cols 9-12)
Row 3: AI Voice Interface (cols 1-8) | Safety Monitor (cols 9-12)
```

**AI Voice Interface Panel** (Horizontal Layout):
- Left section: Wake word status + AI response text
- Right section: Wide spectrogram canvas showing real-time audio
- Mic button: Click to start/stop voice control

## Tracking Modes

The system supports two tracking strategies:

- **Reactive Mode:** Uses LDR sensor differences to follow the sun
- **Predictive Mode:** Uses astronomical calculations (time/location) to track sun position

Users can switch modes via voice ("Helios, switch to predictive mode") or dashboard controls.

## Digital Twin Concept

The system uses "micro-dither sampling" - briefly testing alternative positions to gather A/B comparison data. This data is published via `ai_performance_delta` WebSocket event and proves which tracking strategy is better with real measurements.

## Current Development Status

**Working:**
- Dashboard single-service architecture
- Browser-based voice control with Web Audio API
- Real-time spectrogram visualization
- WebSocket communication for Arduino data
- Dashboard UI with all panels

**In Testing:**
- Wake word detection (currently bypassed - always returns True)
- Gemini audio processing (currently using mock responses)

**Next Steps:**
1. Implement actual wake word detection in `voice_handler.py`
2. Replace mock responses with real Gemini API calls
3. Test end-to-end voice control flow with Arduino

## Troubleshooting

**Dashboard fails to start:**
- Check logs: `tail -f /tmp/helios_dashboard.log`
- Verify .env file has GOOGLE_GENAI_API_KEY
- Check port 5000 is not in use: `lsof -i :5000`

**Voice control not working:**
- Check browser console for errors
- Verify microphone permissions granted
- Test mic access: `navigator.mediaDevices.getUserMedia({audio: true})`
- Check Gemini API key is valid

**Spectrogram not updating:**
- Check if Web Audio API is connected: `console.log(window.aiVoiceInterface.isListening)`
- Verify mic button was clicked to start recording
- Check canvas element exists: `document.getElementById('spectrogramCanvas')`

**Arduino not connected:**
- Dashboard will still run in mock data mode
- Check USB connection and serial port permissions
- Verify Arduino is sending JSON messages with `\n` terminator
