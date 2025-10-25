# Helios AI - System Architecture

## Overview

Helios uses a **direct Arduino-to-computer** architecture with WebSocket-based communication for real-time data streaming and control.

```
┌─────────────────────────────────────────────────────────────┐
│                     Computer (Development Machine)          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Serial WebSocket Bridge                      │  │
│  │  • Reads Arduino via USB                             │  │
│  │  • Broadcasts data to WebSocket clients              │  │
│  │  • Forwards commands to Arduino                      │  │
│  │  • Port: 5000                                        │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               │ WebSocket                                   │
│               │                                             │
│  ┌────────────┴────────────┬───────────────┬─────────────┐ │
│  │                         │               │             │ │
│  │                         │               │             │ │
│  ▼                         ▼               ▼             ▼ │
│ ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌──────┐ │
│ │Dashboard │  │ Voice Agent  │  │AI Logic    │  │Safety│ │
│ │(Flask)   │  │(Google ADK)  │  │(Tracking)  │  │      │ │
│ └──────────┘  └──────────────┘  └────────────┘  └──────┘ │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │ USB Serial
                       │ (9600 baud)
                       ▼
           ┌────────────────────────┐
           │      Arduino           │
           │  • LDR sensors         │
           │  • INA219 (power)      │
           │  • Pan/Tilt servos     │
           │  • Energy tracking     │
           └────────────────────────┘
```

---

## Components

### 1. Arduino (Hardware Layer)
**Responsibilities:**
- Read LDR sensors (4 channels: TL, TR, BL, BR)
- Measure voltage, current, power (via INA219)
- Track cumulative energy saved (kWh)
- Control pan servo (0-180°)
- Control tilt servo (0-180°)
- Implement basic safety limits
- Send JSON data over serial
- Receive JSON commands over serial

**Communication:** USB Serial @ 9600 baud

**See:** [Arduino Protocol Documentation](ARDUINO_PROTOCOL.md)

---

### 2. Serial WebSocket Bridge
**File:** `services/serial_websocket_bridge.py`

**Responsibilities:**
- Connect to Arduino via USB serial
- Parse incoming JSON messages from Arduino
- Broadcast data to WebSocket clients
- Listen for WebSocket commands from clients
- Forward commands to Arduino
- Auto-reconnect on disconnect
- Provide connection status

**WebSocket Events Emitted:**
- `sensors_raw` - Sensor data (LDRs, voltage, current, power)
- `status` - System status (mode, servo angles)
- `impact` - Energy metrics (energy_saved_kWh)
- `safety` - Safety alerts (from Arduino)
- `connection_status` - Arduino connection state

**WebSocket Events Received:**
- `command_position` - Move servos to position
- `command_mode` - Switch tracking mode

**Port:** 5000 (configurable via `DASHBOARD_PORT` in `.env`)

---

### 3. Safety Monitor
**File:** `services/safety_monitor.py`

**Responsibilities:**
- Monitor all incoming data for safety violations
- Check servo angle limits (0-180° for both pan and tilt)
- Check servo movement rate (max 30°/sec)
- Check voltage/current/power limits
- Check temperature (if available)
- Emit safety alerts via WebSocket

**Safety Limits:**
```python
pan_angle: 0-180°
tilt_angle: 0-180°
max_temperature: 80°C
max_voltage: 6.0V
max_current: 500mA
max_power: 3000mW
max_movement_rate: 30°/sec
```

**Runs as:** Independent service (connects as WebSocket client)

---

### 4. Dashboard (Web UI)
**File:** `dashboard/dashboard.py`

**Responsibilities:**
- Visualize real-time sensor data
- Display current power generation
- Show servo positions and sun position
- Display energy saved metrics
- Show safety status
- Provide manual control interface
- Calculate CO2 savings and cost impact

**Technology:** Flask + Flask-SocketIO + Chart.js

**Port:** Same as WebSocket bridge (5000)

---

### 5. Voice Agent (Google ADK)
**File:** `adk/helios_agent/agent.py`

**Responsibilities:**
- Voice-controlled interface for Helios
- Natural language understanding
- Real-time status queries
- Mode switching commands
- Manual positioning commands
- Performance comparisons
- Impact reporting

**Tools:**
- `get_status()` - Current system state
- `switch_mode(mode)` - Change tracking mode
- `move_to(pan, tilt)` - Manual positioning
- `explain_delta()` - A/B performance comparison
- `get_impact()` - Energy/cost/CO2 metrics
- `get_safety_status()` - Safety monitoring

**Model:** gemini-2.5-flash-native-audio-dialog

**Port:** 8000 (for web UI)

---

### 6. AI Logic (Tracking Algorithms)
**File:** `agents/ai_logic.py` *(to be created)*

**Responsibilities:**
- Calculate sun position (astronomical tracking)
- Implement Reactive mode (LDR-based tracking)
- Implement Predictive mode (sun calculation)
- Run Digital Twin simulation (A/B testing)
- Emit tracking commands
- Publish performance metrics

**Modes:**
- **Reactive:** Use LDR sensor differences to track
- **Predictive:** Use time/location to calculate sun position

---

## Data Flow

### Arduino → Computer
```
Arduino → USB Serial → Serial Bridge → WebSocket → Clients
```

1. Arduino sends JSON message over serial
2. Serial bridge receives and parses message
3. Bridge emits WebSocket event based on message type
4. All connected clients receive the event

### Computer → Arduino
```
Client → WebSocket → Serial Bridge → USB Serial → Arduino
```

1. Client emits WebSocket command
2. Serial bridge receives command
3. Bridge formats as JSON and sends to Arduino
4. Arduino executes command

---

## WebSocket Events

### From Bridge (Arduino data):
- `sensors_raw` - Sensor readings
- `status` - System status
- `impact` - Energy metrics
- `safety` - Safety alerts
- `connection_status` - Connection state

### From AI Logic:
- `ai_performance_delta` - Digital twin A/B comparison

### From Safety Monitor:
- `safety` - Safety violations

### To Arduino (commands):
- `command_position` - Move servos
- `command_mode` - Switch mode

---

## Setup & Running

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Start Serial Bridge
```bash
python services/serial_websocket_bridge.py
```

### 4. Start Safety Monitor (optional but recommended)
```bash
python services/safety_monitor.py
```

### 5. Start Voice Agent (optional)
```bash
cd adk
source venv/bin/activate
adk web --port 8000 helios_agent
```

---

## Port Configuration

- **5000** - WebSocket bridge + Dashboard
- **8000** - Voice agent web UI

---

## Development Notes

- All services connect as WebSocket clients to the bridge
- The bridge is the only component that talks to Arduino
- Services can be started/stopped independently
- Dashboard and voice agent can run on same or different machines
- Arduino code handles basic safety, computer handles advanced monitoring

---

## Safety Architecture

**Layer 1: Arduino (Hardware)**
- Hard-coded angle limits
- Immediate response
- Cannot be bypassed

**Layer 2: Safety Monitor (Computer)**
- Advanced monitoring
- Rate limiting
- Trend analysis
- Alerts and logging

This dual-layer approach ensures safety even if computer connection is lost.
