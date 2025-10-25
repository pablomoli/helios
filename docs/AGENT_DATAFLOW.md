# Helios Agent Data Flow

## Overview

The Gemini-powered agent can **read** Arduino data and **send** commands back to control the system through the WebSocket bridge.

## Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                          ARDUINO                                 │
│  • Reads sensors (LDRs, voltage, current, power)                │
│  • Controls servos (pan, tilt)                                  │
│  • Tracks energy saved                                          │
└────────────────┬────────────────────────────────▲────────────────┘
                 │ USB Serial                     │
                 │ (Sensor data)                  │ (Commands)
                 ▼                                │
┌─────────────────────────────────────────────────┴────────────────┐
│              SERIAL WEBSOCKET BRIDGE                             │
│  • Reads Arduino serial output                                   │
│  • Broadcasts to WebSocket clients                               │
│  • Forwards commands to Arduino                                  │
└──────┬──────────────────────────────────────────────────▲────────┘
       │ WebSocket Events:                                 │
       │ - sensors_raw                                     │
       │ - status                                          │
       │ - impact                                          │
       │ - safety                                          │
       │                                                   │
       ▼                                                   │
┌──────────────────────────────────────────────────────────────────┐
│                    HELIOS AGENT (Gemini)                         │
│                                                                   │
│  Listeners (Receive Arduino Data):                               │
│  ✅ on_sensors_raw() → stores sensor readings                    │
│  ✅ on_status() → stores system status                           │
│  ✅ on_impact() → stores energy metrics                          │
│  ✅ on_safety() → stores safety alerts                           │
│  ✅ on_performance_delta() → stores A/B comparison               │
│                                                                   │
│  Tools (Agent can call these):                                   │
│  🔍 get_status() → reads latest Arduino data                     │
│  🔍 get_impact() → reads energy saved                            │
│  🔍 get_safety_status() → reads safety status                    │
│  🔍 explain_delta() → analyzes performance                       │
│                                                                   │
│  📤 switch_mode(mode) → sends command to Arduino                 │
│  📤 move_to(pan, tilt) → sends position command                  │
└──────────────┬───────────────────────────────────────────────────┘
               │
               │ WebSocket Commands:
               │ - command_mode
               │ - command_position
               │
               └───────────────────────────────────────────────────┐
                                                                   │
┌──────────────────────────────────────────────────────────────────▼─┐
│                      DASHBOARD (Frontend)                           │
│  • Visualizes real-time data from WebSocket                        │
│  • Displays charts, gauges, status                                 │
│  • Shows voice log from agent                                      │
│  • Manual controls (also sends WebSocket commands)                 │
└─────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────┐
│                    VOICE CONTROL PATH                             │
│                                                                   │
│  You say "computer" → Porcupine detects                          │
│           ↓                                                       │
│  You ask question → Google STT transcribes                       │
│           ↓                                                       │
│  voice_listener.py sends text query → voice_agent_api.py         │
│           ↓                                                       │
│  voice_agent_api.py calls agent tools:                           │
│    • get_status() - reads Arduino sensor data                    │
│    • switch_mode() - sends command to Arduino                    │
│    • etc.                                                        │
│           ↓                                                       │
│  pyttsx3 speaks response (Windows/Linux/macOS)                   │
└──────────────────────────────────────────────────────────────────┘
```

## How Gemini Interacts with Arduino

### 1. Reading Arduino Data

The agent listens to WebSocket events in real-time:

```python
# In agent.py (lines 46-74)

@sio.on('sensors_raw')
def on_sensors_raw(data):
    """Receives sensor data from Arduino"""
    latest_data['sensors'] = data
    # Example data:
    # {
    #   "panel_voltage_V": 4.85,
    #   "panel_current_mA": 150.2,
    #   "panel_power_mW": 728.47,
    #   "ldr_tl": 812,
    #   "ldr_tr": 750,
    #   ...
    # }

@sio.on('status')
def on_status(data):
    """Receives system status"""
    latest_data['status'] = data
    # Example data:
    # {
    #   "mode": "Predictive",
    #   "pan_angle_deg": 112.5,
    #   "tilt_angle_deg": 45.0,
    #   ...
    # }
```

### 2. Agent Tools Access This Data

When you ask a question, the agent uses tools to get data:

```python
# Tool: get_status() (lines 84-109)

@tool
def get_status() -> dict:
    """Get current status from Arduino"""
    init_websocket()  # Connect if not connected

    status = latest_data['status']  # ← Arduino data
    sensors = latest_data['sensors']  # ← Arduino data

    return {
        "mode": status.get('mode'),
        "current_power_mw": sensors.get('panel_power_mW'),
        "pan_angle": status.get('pan_angle_deg'),
        # ... etc
    }
```

**Example Voice Interaction:**
```
You: "computer, what's the status?"
Agent: Calls get_status() → Reads Arduino data
Agent: "The system is in Predictive mode, generating 730 milliwatts..."
```

### 3. Sending Commands to Arduino

The agent can send commands back to Arduino:

```python
# Tool: switch_mode() (lines 112-131)

@tool
def switch_mode(mode: str) -> str:
    """Switch tracking mode"""
    command = {"mode": mode}
    sio.emit("command_mode", command)  # ← Sends to Arduino!
    return f"Switched to {mode} mode"

# Tool: move_to() (lines 134-161)

@tool
def move_to(pan_angle_deg: float, tilt_angle_deg: float) -> str:
    """Move servos to position"""
    command = {
        "pan_angle_deg": pan_angle_deg,
        "tilt_angle_deg": tilt_angle_deg
    }
    sio.emit("command_position", command)  # ← Sends to Arduino!
    return f"Moving to pan={pan_angle_deg}°, tilt={tilt_angle_deg}°"
```

**Example Voice Interaction:**
```
You: "computer, switch to predictive mode"
Agent: Calls switch_mode("Predictive")
Agent: Sends WebSocket command → Serial Bridge → Arduino
Arduino: Switches mode
Agent: "Switched to Predictive mode. The system will now use astronomical calculations."
```

## Data Flow Steps

### Example: Asking "What's the status?"

1. **You say:** "computer, what's the status?"
2. **voice_listener.py:** Detects wake word, transcribes question
3. **voice_agent_api.py:** Receives text query
4. **voice_agent_api.py:** Calls `get_status()` tool
5. **agent.py:** `get_status()` reads `latest_data['sensors']` and `latest_data['status']`
6. **latest_data:** Contains real-time data from Arduino (received via WebSocket)
7. **agent.py:** Returns formatted status dict
8. **voice_agent_api.py:** Formats response text
9. **pyttsx3:** Speaks: "The system is in Predictive mode, generating 730 milliwatts..."

### Example: Commanding "Switch to reactive mode"

1. **You say:** "computer, switch to reactive mode"
2. **voice_listener.py:** Detects wake word, transcribes command
3. **voice_agent_api.py:** Receives text query, detects "switch" + "reactive"
4. **voice_agent_api.py:** Calls `switch_mode("Reactive")`
5. **agent.py:** `switch_mode()` emits WebSocket event `command_mode` with `{"mode": "Reactive"}`
6. **serial_websocket_bridge.py:** Receives WebSocket command
7. **serial_websocket_bridge.py:** Sends JSON to Arduino over serial
8. **Arduino:** Receives command, switches to Reactive mode
9. **Arduino:** Sends back status update via serial
10. **serial_websocket_bridge.py:** Broadcasts status to all WebSocket clients
11. **Dashboard:** Updates to show "Reactive" mode
12. **pyttsx3:** Speaks: "Switched to Reactive mode. The system will now use sensor-based tracking."

## WebSocket Events Reference

### From Arduino → Agent (via serial bridge)

| Event | Data | Agent Access |
|-------|------|--------------|
| `sensors_raw` | Sensor readings (LDRs, voltage, current, power) | `latest_data['sensors']` |
| `status` | System status (mode, angles, sun position) | `latest_data['status']` |
| `impact` | Energy saved (kWh) | `latest_data['impact']` |
| `safety` | Safety alerts (servo status, temperature) | `latest_data['safety']` |
| `ai_performance_delta` | A/B comparison data | `latest_data['performance_delta']` |

### From Agent → Arduino (via serial bridge)

| Event | Data | Agent Tool |
|-------|------|------------|
| `command_mode` | `{"mode": "Predictive" or "Reactive"}` | `switch_mode()` |
| `command_position` | `{"pan_angle_deg": 90, "tilt_angle_deg": 45}` | `move_to()` |

## Key Points

✅ **The agent ALREADY has access to Arduino data** through WebSocket listeners
✅ **The agent CAN send commands** to Arduino through WebSocket emitters
✅ **This happens in real-time** - no polling needed
✅ **The dashboard sees the same data** - everyone is connected to the same WebSocket
✅ **Voice commands work end-to-end** - from wake word to Arduino control

## Testing the Connection

### Check if agent can read Arduino data:

1. Start serial bridge: `python services/serial_websocket_bridge.py`
2. Start voice agent API: `python services/voice_agent_api.py`
3. Say: "computer, what's the status?"
4. Agent should speak current power, angles, and mode

### Check if agent can send commands:

1. Say: "computer, switch to predictive mode"
2. Arduino should switch modes
3. Dashboard should update to show "Predictive"
4. Agent should confirm: "Switched to Predictive mode..."

## Architecture Summary

The system uses a **hub-and-spoke** model:
- **Hub:** Serial WebSocket Bridge (port 5000)
- **Spokes:**
  - Arduino (via USB serial)
  - Helios Agent (WebSocket client)
  - Dashboard (WebSocket client)
  - Voice Agent API (WebSocket client)

All spokes can:
- **Listen** to data from Arduino
- **Send** commands to Arduino
- **See** the same real-time data

The Gemini agent is just another spoke that happens to have natural language understanding!
