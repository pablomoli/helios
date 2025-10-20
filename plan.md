# Project Plan: Helios AI (Competition Grade v3)

**A voice-first, AI-powered solar tracking platform with a real-time digital twin for intelligent energy optimization and transparent impact reporting.**

---

## 1. Core Concept & Pitch

**Helios AI** is an intelligent energy platform you can talk to. By saying **"Hey Helios,"** you activate a voice-first interface to a system that does more than follow the sun.  
It runs a continuous **digital twin simulation** — using micro-dither sampling to gather real-world data from alternative positions — to A/B test its own tracking strategies in real-time.  
This proves its decisions with hard data.

All system telemetry is streamed over a central **MQTT message bus** and visualized on a live-updating web dashboard, giving a transparent view of the hardware, AI, and environmental impact.

---

## 2. System Architecture & Technology

We will use a robust, real-time, and decoupled architecture.  
The core change is implementing a serial-to-MQTT bridge on the Pi, making the Arduino a simple, reliable sensor/motor controller.

### **Custom Wake Word & Voice Interface**

The voice experience remains a non-negotiable priority.

- We'll use **Picovoice Porcupine** running on the Pi to listen for the custom "Hey Helios" wake word.
- Upon detection, it will immediately trigger the **Google Agent Development Kit (ADK)** to handle natural language understanding and command execution.
- Commands are mapped to tools exposed by the Helios Control Agent.

### **Revised Data Flow Diagram**

1. **Arduino:** Gathers data from LDRs and the INA219 sensor. It writes this data as a simple string to its USB serial port and listens for motor commands on the same port.  
2. **Pi Serial-MQTT Bridge:** Reads serial data, parses it into JSON, and publishes to the MQTT Broker. Subscribes to command topics to send data back to the Arduino.  
3. **MQTT Broker:** Runs on the Pi, managing all message traffic between services.  
4. **Other Services (AI, Web, Voice):** Interact with MQTT, completely decoupled from the hardware.

### **New Agent Layer**

In addition to the Helios Control Agent (voice and command orchestration), two lightweight agents will run alongside it via the **Google ADK**:

1. **Impact Agent** — Calculates environmental and cost benefits in real time.  
   - Subscribes to `helios/sensors/raw` and `helios/ai/performance_delta`  
   - Publishes summarized metrics to `helios/impact`  
   - Tool:  
     ```python
     get_impact(window_s=3600) -> {energy_kWh, usd_saved, co2_g}
     ```

2. **Safety Agent** — Monitors servo limits, motion rate, and temperature.  
   - Subscribes to `helios/status`  
   - Publishes alerts or clamped commands to `helios/safety`  
   - Ensures safe operation under all modes  

### **Revised Circuit Diagram**

- **Power:** Servos must be powered by an external 5V, 2A+ power supply with a large capacitor (1000µF) across the rails to smooth out spikes.  
- **INA219 Power Sensor:** Connects via I2C (SDA=A4, SCL=A5) and measures both voltage and current.  
- **LDRs & Servos:** Remain connected to analog and PWM pins respectively.  
- **Ground:** Common ground shared across Arduino, servo supply, and INA219.

---

## 3. MQTT Topic & Payload Schema

This schema defines the structure of our data for all services and agents.

- **`helios/sensors/raw`**: Published by the serial bridge.  
  ```json
  {
    "timestamp": 1666215482,
    "ldr_tl": 812,
    "ldr_tr": 750,
    "ldr_bl": 550,
    "ldr_br": 532,
    "panel_voltage_V": 4.85,
    "panel_current_mA": 150.2,
    "panel_power_mW": 728.47
  }
  ```

- **`helios/status`**: Published by the Core AI Logic.  
  ```json
  {
    "timestamp": 1666215483,
    "mode": "Predictive",
    "pan_angle_deg": 112.5,
    "tilt_angle_deg": 45.0,
    "sun_azimuth_deg": 115.0,
    "sun_elevation_deg": 46.2,
    "cloud_cover_pct": 15
  }
  ```

- **`helios/command/position`**: Commands for the Arduino.  
  ```json
  {
    "pan_angle_deg": 95.0,
    "tilt_angle_deg": 40.0
  }
  ```

- **`helios/ai/performance_delta`**: Published by the Digital Twin logic.  
  ```json
  {
    "timestamp": 1666215490,
    "window_s": 600,
    "actual_strategy_power_mW": 730.1,
    "shadow_strategy_power_mW": 655.8,
    "delta_pct": 11.33
  }
  ```

- **`helios/impact`**: Published by the Impact Agent.  
  ```json
  {
    "timestamp": 1666215599,
    "energy_kWh": 0.012,
    "usd_saved": 0.03,
    "co2_g": 5.6
  }
  ```

- **`helios/safety`**: Published by the Safety Agent.  
  ```json
  {
    "timestamp": 1666215603,
    "servo_status": "normal",
    "angle_violation": false,
    "temperature_C": 35.2
  }
  ```

---

## 4. The Live Dashboard

The dashboard provides real-time visibility into Helios AI’s decisions, energy output, and impact.

- **Live Sky Map:** Simplified to a single icon/percentage for overall cloud cover.  
- **Real-Time Analytics:** KPIs for Power (mW) and Energy Today (mWh) from INA219 data.  
- **A/B Comparison Graph:** Displays results from the Digital Twin’s micro-dither sampling.

**New Dashboard Panels:**

- **Impact Metrics Panel (Impact Agent):**  
  Displays live CO₂ avoided, cost savings, and total energy gained.  
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

### **Phase 1: Hardware Integration & MQTT Backbone (Hours 0–6)**

- **Goal:** Achieve real sensor communication and manual control over MQTT.  
- **Steps:**
  1. Assemble pre-built chassis with servos, sensors, and wiring.  
  2. Set up Mosquitto MQTT broker on the Pi.  
  3. Code Arduino sketch and Serial-to-MQTT bridge.  
- **Milestone:** View live data and send move commands over MQTT.

---

### **Phase 2: Core Logic & Live Dashboard (Hours 7–14)**

- **Goal:** Implement the AI brain and dashboard.  
- **Steps:**
  1. Build `ai_logic.py` with Reactive and Predictive modes.  
  2. Set up Flask + Flask-SocketIO dashboard.  
  3. Visualize real-time MQTT data.  
- **Milestone:** Autonomously tracking system with live dashboard.

---

### **Phase 3: Custom Wake Word & Voice Control (Hours 15–20)**

- **Goal:** Add branded voice interaction.  
- **Steps:**
  1. Integrate Porcupine wake word “Hey Helios.”  
  2. Link Porcupine → ADK session → voice tools.  
  3. Add voice commands for status and mode switching.  
- **Milestone:** Fully hands-free control via “Hey Helios.”

---

### **Phase 4: The Digital Twin & Final Polish (Hours 21–24+)**

- **Goal:** Implement the micro-dither sampling and “what-if” graph.  
- **Steps:**
  1. Add micro-dither sampling logic to AI.  
  2. Publish `helios/ai/performance_delta`.  
  3. Add “Was predictive mode worth it?” voice command.  
- **Milestone:** Helios AI can prove its decisions with data.

---

### **Phase 5: Impact & Safety Agents (Stretch Goal / Polish)**

- **Goal:** Highlight sustainability and reliability.  
- **Steps:**
  1. Implement `impact_agent.py` (calculates CO₂ and cost savings).  
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
  Porcupine listens for “Hey Helios” → starts ADK session → agent calls tools → TTS replies.

---

## 8. Power & Wiring (Plain-English Checklist)

- Always have a real electrical load for accurate readings.  
- Resistor sizing: R ≈ V² / W (use ≥2× watt rating).  
- High-side wiring: Panel + → INA219 VIN+ → INA219 VOUT+ → resistor → Panel −  
- Common ground across all components.  
- Use a dedicated 5V 2–3A servo power supply with a 1000 µF capacitor.  

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
| CO₂ + Cost Metrics |
+--------------------+
          ↓
+--------------------+
| Safety Agent       |
| Hardware Health    |
+--------------------+
```

---

**Final Outcome:**  
Helios AI becomes an explainable, voice-driven, and sustainability-focused solar tracker that demonstrates measurable impact — perfectly aligned with Google’s ADK innovation goals and OneEthos’ real-world values.
