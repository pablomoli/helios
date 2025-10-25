# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Helios AI is a voice-controlled solar tracking system with real-time Arduino hardware integration. The system uses WebSocket-based hub-and-spoke architecture where all services communicate through a central Serial WebSocket Bridge (port 5000).

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
PORCUPINE_API_KEY=your_key_here          # Free from console.picovoice.ai
OPENWEATHER_API_KEY=your_key_here        # Free from openweathermap.org
WEBSOCKET_SERVER_URL=ws://localhost:5000
DASHBOARD_PORT=5000
```

**Security:** Never commit `.env` file. It's in `.gitignore`.

## Running the System

The system requires multiple services running concurrently. Use separate terminals or tmux.

### Minimal Setup (Voice Control Only)

```bash
# Terminal 1: Voice Agent API (handles queries + TTS)
python services/voice_agent_api.py

# Terminal 2: Voice Listener (wake word detection + STT)
python services/voice_listener.py
```

### Full System (with Arduino)

```bash
# Terminal 1: Serial Bridge (Arduino ↔ WebSocket)
python services/serial_websocket_bridge.py

# Terminal 2: Voice Agent API
python services/voice_agent_api.py

# Terminal 3: Voice Listener
python services/voice_listener.py

# Terminal 4: Dashboard (optional)
python dashboard/dashboard.py
```

## Architecture: Hub-and-Spoke WebSocket Model

**Critical Concept:** The Serial WebSocket Bridge is the ONLY component that communicates with Arduino. All other services are WebSocket clients that connect to the bridge.

```
┌─────────────────────────────────────────────────┐
│     Serial WebSocket Bridge (Port 5000)         │
│     • Reads Arduino USB serial                  │
│     • Broadcasts to all WebSocket clients       │
│     • Forwards commands to Arduino              │
└──────────┬──────────────────────────────────────┘
           │ WebSocket Hub
           │
    ┌──────┴──────┬──────────┬──────────┬─────────┐
    │             │          │          │         │
    ▼             ▼          ▼          ▼         ▼
Dashboard   Voice Agent  Safety    AI Logic  (any client)
            (Gemini)     Monitor
```

### WebSocket Events

**From Arduino (via bridge):**
- `sensors_raw` - LDR sensors, voltage, current, power (every 1-2s)
- `status` - Mode, pan/tilt angles, sun position
- `impact` - Energy saved (kWh)
- `safety` - Safety alerts, servo health, temperature
- `ai_performance_delta` - A/B comparison data

**To Arduino (via bridge):**
- `command_position` - Move servos: `{"pan_angle_deg": 90, "tilt_angle_deg": 45}`
- `command_mode` - Switch mode: `{"mode": "Predictive"}` or `{"mode": "Reactive"}`

**Important:** WebSocket events use centralized constants from `config.config.Events` class.

## Voice Control System

Voice control uses a three-stage pipeline optimized for wake-word triggered single-shot responses.

### Components

1. **voice_listener.py** - Porcupine wake word ("computer") + Google STT
2. **voice_agent_api.py** - Keyword-based query routing + pyttsx3 TTS (cross-platform)
3. **adk/helios_agent/agent.py** - Gemini agent with tools that read/control Arduino

### Voice Flow

```
Say "computer" → Porcupine detects → Say question → Google STT transcribes
                                                    ↓
                                    voice_listener sends text via WebSocket
                                                    ↓
                            voice_agent_api.py routes to agent tools
                                                    ↓
                                Agent tool reads latest_data or sends command
                                                    ↓
                            pyttsx3 speaks response (Windows/Linux/macOS)
```

### Gemini Agent Integration

The agent in `adk/helios_agent/agent.py` has two types of tools:

**Read Tools** (access Arduino data):
- `get_status()` - Reads `latest_data['sensors']` and `latest_data['status']`
- `get_impact()` - Reads `latest_data['impact']`
- `get_safety_status()` - Reads `latest_data['safety']`
- `explain_delta()` - Reads `latest_data['performance_delta']`

**Control Tools** (send commands to Arduino):
- `switch_mode(mode)` - Emits `command_mode` WebSocket event
- `move_to(pan, tilt)` - Emits `command_position` WebSocket event

**Critical:** The agent maintains a global `latest_data` dict that's automatically updated by WebSocket listeners. Tools access this dict for real-time Arduino data.

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

The `type` field determines how `serial_websocket_bridge.py` routes the data to WebSocket events.

## Configuration System

All services use `config.config.Config` for centralized configuration:

```python
from config.config import Config, Events

# Access config
Config.WEBSOCKET_SERVER_URL  # ws://localhost:5000
Config.OPENWEATHER_API_KEY   # Never log this!

# Use event constants
sio.emit(Events.COMMAND_MODE, {"mode": "Predictive"})
sio.on(Events.SENSORS_RAW, handler_function)
```

**Safe config display:**
```python
print(Config.get_safe_config_string())  # Hides secrets
```

## Key Design Patterns

### Pattern 1: WebSocket Client Initialization

All services that connect to the bridge follow this pattern:

```python
import socketio
from config.config import Config, Events

sio = socketio.Client()

# Define event handlers BEFORE connecting
@sio.on(Events.SENSORS_RAW)
def on_sensors(data):
    # Process sensor data
    pass

# Connect to bridge
sio.connect(Config.WEBSOCKET_SERVER_URL)
```

### Pattern 2: Agent Tool with Latest Data

Agent tools read from the global `latest_data` dict that's updated by WebSocket listeners:

```python
@tool
def get_status() -> dict:
    """Get current status from Arduino"""
    init_websocket()  # Ensure connected

    # Read latest data (updated by WebSocket listeners)
    status = latest_data['status']
    sensors = latest_data['sensors']

    return {
        "mode": status.get('mode'),
        "current_power_mw": sensors.get('panel_power_mW')
    }
```

### Pattern 3: Sending Commands to Arduino

Commands are sent via WebSocket to the bridge, which forwards to Arduino:

```python
@tool
def switch_mode(mode: str) -> str:
    """Switch tracking mode"""
    init_websocket()

    # Emit command via WebSocket
    sio.emit("command_mode", {"mode": mode})

    return f"Switched to {mode} mode"
```

## Testing

```bash
# Test config loading
python config/config.py

# Test weather service
python services/weather_service.py

# Test Arduino communication (without WebSocket)
python services/serial_bridge.py

# Test TTS
python -c "import pyttsx3; e=pyttsx3.init(); e.say('test'); e.runAndWait()"
```

## Common Development Tasks

### Adding a New WebSocket Event

1. Add event constant to `config/config.py` in `Events` class
2. Update Arduino to send new JSON message type
3. Update `serial_websocket_bridge.py` to handle the message
4. Add listener in relevant service (agent, dashboard, etc.)

### Adding a New Voice Command

1. Add keyword detection in `voice_agent_api.py` `handle_voice_query()`
2. Create new agent tool in `adk/helios_agent/agent.py` if needed
3. Update agent instructions to explain the new capability

### Debugging WebSocket Communication

```python
# Add verbose logging to any WebSocket client
@sio.on('*')
def catch_all(event, data):
    print(f"Event: {event}, Data: {data}")
```

## Important Constraints

1. **Dashboard files:** Do NOT modify dashboard files unless explicitly requested by user
2. **Security:** Never commit `.env` file or log API keys
3. **Arduino safety:** Always validate servo angles (0-180°) before sending commands
4. **WebSocket routing:** Only the Serial WebSocket Bridge talks to Arduino directly
5. **Voice responses:** Keep agent responses concise (1-3 sentences) for TTS clarity
6. **Platform compatibility:** TTS uses pyttsx3 (Windows SAPI / macOS NSSpeechSynthesizer / Linux espeak)

## Project Structure

```
helios/
├── adk/
│   └── helios_agent/
│       └── agent.py              # Gemini agent with tools
├── config/
│   └── config.py                 # Centralized config + Events
├── dashboard/
│   └── dashboard.py              # Flask web UI (DO NOT MODIFY)
├── docs/
│   ├── SYSTEM_ARCHITECTURE.md    # Detailed architecture
│   ├── ARDUINO_PROTOCOL.md       # Serial protocol spec
│   ├── VOICE_SETUP.md           # Voice system setup
│   └── AGENT_DATAFLOW.md        # Agent ↔ Arduino integration
├── services/
│   ├── serial_websocket_bridge.py   # WebSocket hub (talks to Arduino)
│   ├── voice_listener.py            # Wake word + STT
│   ├── voice_agent_api.py           # Query routing + TTS
│   ├── weather_service.py           # OpenWeatherMap API
│   └── safety_monitor.py            # Safety checks
├── .env                          # Secrets (never commit!)
├── requirements.txt              # Python dependencies
└── VOICE_QUICKSTART.md          # Quick voice setup guide
```

## Tracking Modes

The system supports two tracking strategies:

- **Reactive Mode:** Uses LDR sensor differences to follow the sun
- **Predictive Mode:** Uses astronomical calculations (time/location) to track sun position

Users can switch modes via voice ("computer, switch to predictive mode") or dashboard.

## Digital Twin Concept

The system uses "micro-dither sampling" - briefly testing alternative positions to gather A/B comparison data. This data is published via `ai_performance_delta` WebSocket event and proves which tracking strategy is better with real measurements.
