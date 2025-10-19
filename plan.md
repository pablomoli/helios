# Project Plan: Helios AI (Competition Grade)

**A voice-first, AI-powered solar tracking platform with a real-time digital twin for intelligent energy optimization.**

---

## 1. Core Concept & Pitch

**Helios AI** is not just a solar tracker; it's an intelligent energy platform you can talk to. By saying **"Hey Helios,"** you activate a voice-first interface to a system that does more than follow the sun. It runs a continuous **digital twin simulation**, A/B testing its own tracking strategies in real-time to prove it's making the optimal decision. All system data is streamed over a central **MQTT message bus** and visualized on a live-updating web dashboard, giving a complete, transparent view of the hardware and AI's performance.

---

## 2. System Architecture & Technology

We are moving away from simple files to a robust, real-time, and decoupled architecture using an MQTT message bus. This is a standard and impressive pattern for IoT projects.

### **Custom Wake Word: "Hey Helios"**

We'll use **Picovoice Porcupine**, a lightweight and highly accurate wake word engine that runs entirely on the Raspberry Pi.

1. The Porcupine engine constantly listens for "Hey Helios."
2. When detected, it triggers the Google Assistant SDK to start listening for the rest of the command (e.g., "...what's the current power output?").
3. This creates a seamless, branded voice experience.

### **Data Flow Diagram**

This diagram illustrates how all the components communicate via the MQTT Broker running on the Raspberry Pi.

- **Arduino:** Publishes raw sensor data to `helios/sensors`. Subscribes to `helios/command/position` to receive pan/tilt instructions.
- **Core AI Logic (Python):** Subscribes to `helios/sensors`. Publishes processed data and decisions to `helios/status` and `helios/ai_state`. Sends commands to `helios/command/position`.
- **Flask Web Server (Python):** Subscribes to all `helios/status/+` and `helios/ai_state/+` topics to gather data for the dashboard.
- **Voice Service (Python):** Subscribes to `helios/status/summary` for quick answers. Publishes commands to `helios/command/mode` or `helios/command/system`.
- **Web Dashboard (Browser):** A JavaScript client connects to the Flask server via **WebSockets** for a persistent, real-time data stream.

### **Circuit Diagram**

This diagram shows the exact wiring for the Arduino Uno. It's designed for simplicity and reliability.

- **Power:** Servos should ideally be powered from an external 5V source, but for a hackathon, they can be run from the Arduino's 5V pin if the movements are slow and infrequent.
- **LDRs:** Each of the four LDRs is in a voltage divider circuit with a 10kΩ resistor.
- **Servos:** Pan servo connects to pin `~9`, Tilt servo to pin `~10`.
- **Solar Panel:** The small solar panel's output is measured via a voltage sensor module connected to analog pin `A2`.

---

## 3. The Live Dashboard

The dashboard is a critical piece of the presentation. It will be a single-page web application served by Flask, using WebSockets to receive a live stream of JSON data.

- **Live Sky Map:** An SVG-based visualization showing:
  - The sun's calculated path across the sky.
  - A "sun" icon that moves along the path based on the time of day.
  - A "panel" icon showing the tracker's current pan/tilt orientation.
  - Overlaid cloud icons fetched from the weather API for the relevant sky quadrant.
- **System Status Module:**
  - **Raspberry Pi:** Live graphs for CPU and memory usage.
  - **Arduino:** A "status light" (green/red) indicating connection status and the last sensor data packet received.
- **Real-Time Analytics:**
  - A live line graph showing power generation over the last 15 minutes.
  - Key performance indicators (KPIs) like "Current Power," "AI Mode," and "Energy Today."

---

## 4. Unique Phase 4 Feature: The Digital Twin

This is the advanced feature that will set Helios AI apart.

- **Concept:** The AI doesn't just pick one strategy; it simulates others in parallel.
- **Execution:**
  1. When the AI is in **Predictive Mode**, the main logic moves the panel based on its forecast-adjusted calculations.
  2. Simultaneously, a **"Shadow Logic"** process runs in the background. It calculates where the panel _would_ have pointed if it were in the dumber **Reactive Mode** (just following the brightest spot).
  3. It then uses the live LDR sensor data to estimate the power output it _would_ have gotten from that reactive position.
  4. The AI constantly compares its actual performance against the shadow simulation's performance.
- **Voice Interaction:**
  - **User:** _"Hey Helios, was predictive mode worth it?"_
  - **Helios AI:** _"Yes. Over the last 30 minutes, my predictive tracking generated an estimated 14% more power compared to the simulated reactive tracking, which would have been pointed toward that cloud bank."_
- **Dashboard Visualization:** A dedicated graph showing the real power output line versus a dotted "what-if" power output line from the simulation.

---

## 5. Updated Hackathon Plan

#### **Phase 1: Platform & MQTT Backbone (Hours 0-6)**

- **Goal:** A controllable tracker with a centralized messaging system.
- **Steps:**
  1. Start the 3D print for the pan-tilt mechanism.
  2. Set up a Mosquitto MQTT broker on the Raspberry Pi.
  3. Code the Arduino sketch to publish sensor JSON to `helios/sensors` and subscribe to `helios/command/position`.
  4. Write a simple test Python script on the Pi to publish position commands and verify that the tracker moves.
- **Milestone:** You have a decoupled hardware platform that can be controlled from any MQTT client.

#### **Phase 2: Core Logic & Live Dashboard (Hours 7-14)**

- **Goal:** Implement the AI's brain and the primary visual interface.
- **Steps:**
  1. Develop the main `ai_logic.py` script that subscribes to sensors and implements both **Reactive** and **Predictive** modes.
  2. Set up the Flask server with a WebSocket endpoint.
  3. Write a Python service that subscribes to all relevant MQTT topics and forwards them to the web dashboard via WebSockets.
  4. Develop the front-end JavaScript to render the **Live Sky Map** and status modules.
- **Milestone:** The tracker moves autonomously, and you can see its status in real-time on the web dashboard.

#### **Phase 3: Custom Wake Word & Voice Control (Hours 15-20)**

- **Goal:** Integrate the branded, hands-free voice interface.
- **Steps:**
  1. Install and configure the **Picovoice Porcupine** engine on the Pi with "Hey Helios" as the wake word.
  2. Write the script that links Picovoice to the Google Assistant SDK.
  3. Implement the basic voice commands (status report, mode switch) which will publish messages to the `helios/command` MQTT topics.
- **Milestone:** You can say "Hey Helios, switch to predictive mode," and see the change reflected on the dashboard as the tracker moves.

#### **Phase 4: The Digital Twin & Final Polish (Hours 21-24+)**

- **Goal:** Implement the "wow" feature and prepare for the demo.
- **Steps:**
  1. Add the **Shadow Simulation** logic into your main AI script.
  2. Create new MQTT topics like `helios/ai_state/shadow_power` and `helios/ai_state/performance_delta`.
  3. Add the comparison graph to the web dashboard.
  4. Implement the "Explain your logic" or "Was it worth it?" voice command.
  5. Refine the demo script and practice your pitch.
- **Milestone:** Helios AI is a fully integrated, intelligent platform that can not only act but also justify its actions with data.
