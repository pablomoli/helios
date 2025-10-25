# Project Plan: Helios AI (Competition Grade v3)

A voice-first, AI-powered solar tracking platform with a real-time digital twin for intelligent energy optimization and transparent impact reporting.

---

## 1. Core Concept & Pitch

Helios AI is an intelligent energy platform you can talk to. By saying "Hey Helios," you activate a voice-first interface to a system that does more than follow the sun.  
It runs a continuous digital twin simulation -- using micro-dither sampling to gather real-world data from alternative positions -- to A/B test its own tracking strategies in real-time.  
This proves its decisions with hard data.

All system telemetry is streamed over WebSocket connections and visualized on a live-updating web dashboard, giving a transparent view of the hardware, AI, and environmental impact.

---

## 2. System Architecture & Technology

The system uses a WebSocket-based architecture for real-time communication between components.

    Backend Server: Runs the WebSocket server and interfaces with the Arduino. It handles all hardware communication and serves sensor data to connected clients while accepting commands from the web interface.

    M3 MacBook Pro (Development Machine): This is where you run the AI logic, the Flask dashboard, all ADK agents (Control, Impact, Safety), and the Porcupine wake word engine, utilizing the Mac's superior processing power and native audio I/O.

### Network Configuration

All application services on the Mac will be configured to connect to the WebSocket server using the server's URL (e.g., ws://localhost:5000 for local development).

### Data Flow Diagram

    Arduino: Gathers sensor data (LDRs, INA219), writes it to its USB serial port, and listens for motor commands.

    Backend Server:

        Runs the WebSocket Server (using Flask-SocketIO).

        Runs a Serial-to-WebSocket Bridge script that reads the Arduino's serial output, parses it into JSON, and emits it to all connected WebSocket clients. It also listens for command events to send instructions back to the Arduino.

    MacBook Pro:

        All agents, the AI logic, and the dashboard connect to the WebSocket server.

        Voice commands are processed on the Mac, which then emits motor commands to the WebSocket server.

### New Agent Layer

In addition to the Helios Control Agent, two lightweight agents will run alongside it on the MacBook Pro via the Google ADK:

    Impact Agent -- Calculates environmental and cost benefits in real time.

        Listens to sensors_raw and ai_performance_delta WebSocket events.

        Emits summarized metrics via the impact event.

    Safety Agent -- Monitors servo limits, motion rate, and temperature.

        Listens to the status WebSocket event.

        Emits alerts or clamped commands via the safety event.

### Revised Circuit Diagram

    Power: Servos are powered by an external 5V, 2A+ power supply with a 1000uF capacitor across the rails.

    INA219 Power Sensor: Connects via I2C (SDA=A4, SCL=A5) and measures voltage and current.

    LDRs & Servos: Remain connected to analog and PWM pins respectively.

    Ground: A common ground is shared across the Arduino, servo supply, and INA219.

---

## 3. WebSocket Events & Payload Schema

This schema defines the data structure for WebSocket events.

    sensors_raw: Raw sensor data from the backend server.
    JSON

{ "timestamp": 1666215482, "ldr_tl": 812, "ldr_tr": 750, "ldr_bl": 550, "ldr_br": 532, "panel_voltage_V": 4.85, "panel_current_mA": 150.2, "panel_power_mW": 728.47 }

status: System status from the Core AI Logic.
JSON

{ "timestamp": 1666215483, "mode": "Predictive", "pan_angle_deg": 112.5, "tilt_angle_deg": 45.0, "sun_azimuth_deg": 115.0, "sun_elevation_deg": 46.2, "cloud_cover_pct": 15 }

command_position: Position commands for the Arduino.
JSON

{ "pan_angle_deg": 95.0, "tilt_angle_deg": 40.0 }

ai_performance_delta: Digital Twin comparison data.
JSON

{ "timestamp": 1666215490, "window_s": 600, "actual_strategy_power_mW": 730.1, "shadow_strategy_power_mW": 655.8, "delta_pct": 11.33 }

impact: Data from the Impact Agent.
JSON

{ "timestamp": 1666215599, "energy_kWh": 0.012, "usd_saved": 0.03, "co2_g": 5.6 }

safety: Data from the Safety Agent.
JSON

    { "timestamp": 1666215603, "servo_status": "normal", "angle_violation": false, "temperature_C": 35.2 }

---

## 4. The Live Dashboard

The dashboard runs on the MacBook Pro, providing real-time visibility into Helios AI.

    Live Sky Map: Simplified to a single icon/percentage for overall cloud cover.

    Real-Time Analytics: KPIs for Power (mW) and Energy Today (mWh).

    A/B Comparison Graph: Displays results from the Digital Twin's micro-dither sampling.

    Impact Metrics Panel (Impact Agent): Displays live CO2 avoided, cost savings, and total energy gained.

    Safety Monitor (Safety Agent): Shows servo health and system safety status.

    Voice Log: Shows the latest commands and AI responses for transparency.

---

## 5. Unique Feature: The Digital Twin (Micro-Dither Method)

The Digital Twin logic runs on the MacBook Pro.

    The AI logic determines the optimal position (Position A).

    It calculates an alternative position (Position B) from the "shadow" logic.

    It commands the tracker to move briefly to Position B, samples power, then returns to Position A.

    It publishes both readings to helios/ai/performance_delta.

---

## 6. Updated Hackathon Plan

### Phase 1: Hardware & Network Backbone (Hours 0-6)

    Goal: Establish the connection and achieve manual control.

    Steps:

        Assemble chassis, servos, sensors, and wiring.

        Set up WebSocket server (Flask-SocketIO).

        Code Arduino sketch and the Serial-to-WebSocket bridge.

        Test WebSocket connection and data flow.

    Milestone: Manually emit a move command and see the physical tracker respond, while viewing sensor data streamed via WebSocket.

---

### Phase 2: Core Logic & Live Dashboard (Hours 7-14)

    Goal: Implement the AI brain and dashboard.

    Steps:

        Build ai_logic.py, connecting to the WebSocket server.

        Set up Flask + Flask-SocketIO dashboard.

        Visualize real-time data coming via WebSocket.

    Milestone: System autonomously tracks the sun, with the dashboard showing live data.

---

### Phase 3: Custom Wake Word & Voice Control (Hours 15-20)

    Goal: Add voice interaction.

    Steps:

        Integrate Porcupine wake word "Hey Helios".

        Link Porcupine → ADK session → voice tools.

        Add voice commands for status and mode switching.

    Milestone: Fully hands-free control via "Hey Helios."

---

### Phase 4: The Digital Twin & Final Polish (Hours 21-24+)

    Goal: Implement the micro-dither sampling logic.

    Steps:

        Add micro-dither logic to the AI.

        Emit ai_performance_delta event.

        Add "Was predictive mode worth it?" voice command.

    Milestone: Helios AI can prove its decisions with data.

---

### Phase 5: Impact & Safety Agents (Stretch Goal / Polish)

    Goal: Highlight sustainability and reliability.

    Steps:

        Implement impact_agent.py and safety_agent.py.

        Add both panels to the dashboard.

    Milestone: Dashboard shows live impact and safety indicators.

---

## 7. ADK + Wake Word Integration

    Packages: pip install google-adk python-socketio python-dotenv

    Scaffold: adk create helios_agent, then edit helios_agent/agent.py to expose tools.

    Run/Dev:

        CLI: adk run helios_agent

        Web UI (mic supported): adk web --port 8000 helios_agent

    Voice Path: Porcupine listens for "Hey Helios" → starts ADK session → agent calls tools → emits WebSocket events → TTS replies.

---

## 8. Power & Wiring

(This section remains unchanged as the physical wiring is identical.)

    Always have a real electrical load for accurate readings.

    Resistor sizing: R≈V2/W (use ≥2× watt rating).

    High-side wiring: Panel + → INA219 VIN+ → INA219 VOUT+ → resistor → Panel −.

    Common ground across all components.

    Use a dedicated 5V 2-3A servo power supply with a 1000 uF capacitor.

---

## 9. Process Management

Services to run (Backend Server)

The backend server runs:

    Flask-SocketIO WebSocket server

    serial_bridge.py (The Python script connecting the Arduino to WebSocket)

Services to run (Development Machine)

Use tmux or multiple terminal tabs for development.

    Set Environment Variable: Before running any service, set the WebSocket server URL:
    Bash

    export WEBSOCKET_SERVER_URL='ws://localhost:5000'

    Run Services:

        python dashboard.py

        python ai_logic.py

        python impact_agent.py

        python safety_agent.py

        python porcupine_wake.py

        adk run helios_agent

---

## 10. Agent Overview Diagram

(This high-level diagram remains conceptually the same.)

+--------------------+
| Helios Control     |
| Voice + Commands   |
+--------------------+
          ↓
+--------------------+
| Impact Agent       |
| CO2 + Cost Metrics |
+--------------------+
          ↓
+--------------------+
| Safety Agent       |
| Hardware Health    |
+--------------------+

---

Final Outcome: Helios AI becomes an explainable, voice-driven, and sustainability-focused solar tracker that demonstrates measurable impact. The distributed development model ensures a smooth, powerful, and efficient workflow, perfectly suited for a competitive hackathon environment.
    "temperature_C": 35.2
  }
  ```

---

## 4. The Live Dashboard

The dashboard provides real-time visibility into Helios AI's decisions, energy output, and impact.

- **Live Sky Map:** Simplified to a single icon/percentage for overall cloud cover.  
- **Real-Time Analytics:** KPIs for Power (mW) and Energy Today (mWh) from INA219 data.  
- **A/B Comparison Graph:** Displays results from the Digital Twin's micro-dither sampling.

**New Dashboard Panels:**

- **Impact Metrics Panel (Impact Agent):**  
  Displays live CO2 avoided, cost savings, and total energy gained.  
  Source: `helios/impact`

- **Safety Monitor (Safety Agent):**  
  Shows servo health and system safety status (✅ Normal / ⚠ Alert).  
  Source: `helios/safety`

- **Voice Log:**  
  Shows the latest commands and AI responses for transparency.

---

## 5. Unique Feature: The Digital Twin (Micro-Dither Method)

The Digital Twin uses a fast, data-driven sampling method:

1. The AI logic determines the optimal position (Position A) based on its current mode.  
2. It calculates an alternative position (Position B) from the "shadow" logic.  
3. It moves briefly to Position B, samples power, then returns to Position A.  
4. It publishes both readings to `helios/ai/performance_delta`.  

This allows the system to justify its decisions with quantifiable, real-world data.

---

## 6. Updated Hackathon Plan

### **Phase 1: Hardware Integration & MQTT Backbone (Hours 0-6)**

- **Goal:** Achieve real sensor communication and manual control over MQTT.  
- **Steps:**
  1. Assemble pre-built chassis with servos, sensors, and wiring.  
  2. Set up Mosquitto MQTT broker on the Pi.  
  3. Code Arduino sketch and Serial-to-MQTT bridge.  
- **Milestone:** View live data and send move commands over MQTT.

---

### **Phase 2: Core Logic & Live Dashboard (Hours 7-14)**

- **Goal:** Implement the AI brain and dashboard.  
- **Steps:**
  1. Build `ai_logic.py` with Reactive and Predictive modes.  
  2. Set up Flask + Flask-SocketIO dashboard.  
  3. Visualize real-time MQTT data.  
- **Milestone:** Autonomously tracking system with live dashboard.

---

### **Phase 3: Custom Wake Word & Voice Control (Hours 15-20)**

- **Goal:** Add branded voice interaction.  
- **Steps:**
  1. Integrate Porcupine wake word "Hey Helios."  
  2. Link Porcupine → ADK session → voice tools.  
  3. Add voice commands for status and mode switching.  
- **Milestone:** Fully hands-free control via "Hey Helios."

---

### **Phase 4: The Digital Twin & Final Polish (Hours 21-24+)**

- **Goal:** Implement the micro-dither sampling and "what-if" graph.  
- **Steps:**
  1. Add micro-dither sampling logic to AI.  
  2. Publish `helios/ai/performance_delta`.  
  3. Add "Was predictive mode worth it?" voice command.  
- **Milestone:** Helios AI can prove its decisions with data.

---

### **Phase 5: Impact & Safety Agents (Stretch Goal / Polish)**

- **Goal:** Highlight sustainability and reliability.  
- **Steps:**
  1. Implement `impact_agent.py` (calculates CO2 and cost savings).  
  2. Implement `safety_agent.py` (monitors servo limits and publishes alerts).  
  3. Add both panels to the dashboard.  
- **Milestone:** Dashboard shows live impact metrics and safety indicators.

---

## 7. ADK + Wake Word Integration (Non-Negotiable)

- **Packages:**  
  `pip install google-adk paho-mqtt python-dotenv`
- **Scaffold:**  
  `adk create helios_agent`, then edit `helios_agent/agent.py` to expose tools:
  - `get_status() -> dict`
  - `switch_mode(mode: str)`
  - `move_to(pan_angle_deg: float, tilt_angle_deg: float)`
  - `explain_delta(window_s: int = 600) -> str`
  - `get_impact(window_s: int = 3600) -> dict`
- **Run/Dev:**  
  - CLI: `adk run helios_agent`  
  - Web UI (mic supported): `adk web --port 8000 helios_agent`
- **Voice Path:**  
  Porcupine listens for "Hey Helios" → starts ADK session → agent calls tools → TTS replies.

---

## 8. Power & Wiring (Plain-English Checklist)

- Always have a real electrical load for accurate readings.  
- Resistor sizing: R ≈ V^2 / W (use ≥2× watt rating).  
- High-side wiring: Panel + → INA219 VIN+ → INA219 VOUT+ → resistor → Panel −  
- Common ground across all components.  
- Use a dedicated 5V 2-3A servo power supply with a 1000 uF capacitor.  

---

## 9. Process Management

- **Services to run:**  
  `mosquitto`, `serial_bridge.py`, `ai_logic.py`, `impact_agent.py`, `safety_agent.py`, `dashboard.py`, `porcupine_wake.py`, `adk agent`
- **Dev:** Use `tmux` with one pane per service.  
- **Startup:** Use `systemd` to auto-start and restart services.

---

## 10. Agent Overview Diagram

```
+--------------------+
| Helios Control     |
| Voice + Commands   |
+--------------------+
          ↓
+--------------------+
| Impact Agent       |
| CO2 + Cost Metrics |
+--------------------+
          ↓
+--------------------+
| Safety Agent       |
| Hardware Health    |
+--------------------+
```

---

**Final Outcome:**  
Helios AI becomes an explainable, voice-driven, and sustainability-focused solar tracker that demonstrates measurable impact -- perfectly aligned with Google's ADK innovation goals and OneEthos' real-world values.
