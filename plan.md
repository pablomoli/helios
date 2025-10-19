# Project Plan: Helios AI

**A voice-first, AI-powered solar tracking platform for intelligent energy optimization.**

---

## Project Pitch

**Helios AI** is a smart solar platform that uses a voice-first interface to deliver truly intelligent energy optimization. Unlike basic trackers, it leverages a 3D-printed, high-precision pan-tilt system as a stable data-gathering platform. The core intelligence runs on a Raspberry Pi, which fuses real-time sky brightness data with predictive weather models. All interactions, from manual control to deep data analysis, are handled through conversational AI, making advanced energy management accessible and intuitive.

---

## Core Technologies

- **Hardware:** Raspberry Pi 3, Arduino Uno, Google Agent Development Kit (ADK), 3D Printer
- **Software:** Python (pyserial, flask, astral), Arduino (C++), Google Assistant SDK
- **APIs:** OpenWeatherMap API for real-time weather data

---

## 3D Printing Strategy

The 3D printer is a strategic asset for creating a professional and reliable hardware base quickly, allowing more time for software development.

- **Action Plan:**
  1.  **Find a Model:** Search on Thingiverse or Printables for a "Arduino Servo Pan Tilt" mechanism compatible with SG90 or similar servos.
  2.  **Download & Print:** Begin the print at the very start of the hackathon to maximize development time.
  3.  **Assemble:** Once the print is complete, assemble the servos and solar panel onto the frame.

---

## Expanded Google ADK Voice Features

The voice interface is the core of the user experience. By logging performance data to a local CSV file, we can enable a rich set of interactions.

#### 1. Conversational Data Analysis 🗣️📈

Enable natural language queries about the system's historical performance.

- _"Hey Google, ask Helios AI what the peak power output was today."_
- _"Hey Google, ask Helios AI to compare this morning's performance to this afternoon's."_
- _"Hey Google, ask Helios AI how much time we spent in predictive mode yesterday."_

#### 2. Proactive Voice Alerts 📢

Allow the device to speak without being prompted to announce autonomous decisions.

- _(Device speaks):_ "Weather forecast has changed. Heavy cloud cover expected in 15 minutes. Switching to reactive LDR mode to find the brightest spot."
- _(Device speaks):_ "System calibration complete. Light sensor variance is within optimal range."

#### 3. Voice-Activated System Commands & Calibration ⚙️

Use voice for system-level functions and manual overrides.

- _"Hey Google, tell Helios AI to run a sky-scan calibration."_
- _"Hey Google, tell Helios AI to reboot its tracking controller."_
- _"Hey Google, tell Helios AI to point directly south."_

#### 4. "Explain Your Logic" Mode (The "Wow" Feature) 🤖❓

This feature allows the AI to explain its decision-making process, demonstrating its intelligence.

- **User:** _"Hey Google, ask Helios AI why it's pointing in that direction."_
- **Helios AI Response:** _"The sun's calculated position is 15 degrees further west, but my weather API reports 90% cloud cover in that direction. I am currently pointing toward a brighter area of the sky with only 30% cloud cover to maximize ambient light capture, which is currently generating 12% more power than pointing directly at the sun's location."_

---

## Hackathon Phased Development Plan

This plan is structured to ensure a demoable product at every stage.

#### **Phase 1: The Platform (Hours 0-5)**

- **Goal:** A solid, controllable physical tracker.
- **Steps:**
  1.  **Start the 3D Print:** Begin printing the pan-tilt mechanism immediately.
  2.  **Assemble Electronics:** Wire the Arduino, servos, LDRs, and voltage sensor on a breadboard.
  3.  **Establish Pi-Arduino Link:** Code the basic Python (`pyserial`) and Arduino scripts for communication. The Pi should be able to command the servos to specific angles.
- **Milestone:** You can manually position the tracker by typing commands into the Pi's terminal.

#### **Phase 2: Core Logic & Data Logging (Hours 6-12)**

- **Goal:** Implement the basic "smart" behavior and the ability to record data.
- **Steps:**
  1.  Code the **Reactive Mode** (follow light) and **Predictive Mode** (use weather API + sun position library) in the main Python script.
  2.  Implement a simple data logger that appends `timestamp, power_mW, pan_angle, tilt_angle, current_mode, cloud_cover_percent` to a `log.csv` file.
- **Milestone:** The tracker moves autonomously and records its own performance history.

#### **Phase 3: Foundational Voice Control (Hours 13-18)**

- **Goal:** Integrate the Google ADK for basic control and reporting.
- **Steps:**
  1.  Set up the Google Assistant SDK on the Raspberry Pi.
  2.  Implement two basic commands: a status report and a mode switch command.
- **Milestone:** You can talk to your project and have it respond and change its behavior.

#### **Phase 4: Advanced Voice Features (Hours 19-24+)**

- **Goal:** Implement one or two of the "wow" features to impress the judges.
- **Steps:**
  1.  **Choose Your Feature:** Select the most impressive feature you are confident in implementing (e.g., "Explain Your Logic" or Proactive Alerts).
  2.  **Code the Logic:** Develop the more advanced Python scripts required for parsing logs or setting up event-driven triggers.
  3.  **Refine & Test:** Spend the final hours making the voice interaction smooth and reliable for the final demo.
- **Milestone:** Helios AI feels less like a machine you command and more like an intelligent agent you collaborate with.
