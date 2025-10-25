# Helios AI Voice Agent (ADK)

Voice-controlled assistant for the Helios solar tracking system using **Google ADK** with **gemini-2.5-flash-native-audio-dialog** model.

## 🎤 What This Does

This agent provides natural voice interaction with your solar tracker using:
- **Direct voice input** (no separate speech-to-text needed)
- **Native voice output** (no separate text-to-speech needed)
- **Low latency** conversation
- **MQTT integration** to control the physical hardware

## 🔐 Security Setup (IMPORTANT!)

**Your API keys are secured and will NOT be pushed to GitHub.**

### First Time Setup:

1. **Virtual environment (already created):**
   ```bash
   # A venv exists at /home/leo/code/helios/adk/venv
   # Activate it with:
   source venv/bin/activate  # when in /home/leo/code/helios/adk
   ```

2. **Get Google API Key:**
   - Go to [Google AI Studio](https://aistudio.google.com/apikey)
   - Create an API key
   - Add it to `helios_agent/.env`:
     ```
     GOOGLE_GENAI_API_KEY=your_key_here
     ```

3. **Configure MQTT broker:**
   - In `helios_agent/.env`, update `MQTT_BROKER_HOST` to your Raspberry Pi's IP
   - Default is `localhost` for testing with mock data

### Verify Security:

```bash
# .env files are in .gitignore
git status

# helios_agent/.env should NOT appear!
```

## 🚀 Quick Start

### CLI Mode (Text Only)
```bash
cd /home/leo/code/helios/adk
source venv/bin/activate
adk run helios_agent
```

### Web UI Mode (Voice Enabled - RECOMMENDED)
```bash
cd /home/leo/code/helios/adk
source venv/bin/activate
adk web --port 8000 helios_agent
```

Then open http://localhost:8000 and click the microphone icon to talk!

## 🎯 Voice Commands Examples

- "Hey Helios, what's the current status?"
- "Switch to predictive mode"
- "How much energy have we generated?"
- "Is predictive mode worth it?"
- "What's the safety status?"
- "Move to pan 90 and tilt 45"

## 🛠️ Available Tools

The agent has 6 tools to control and monitor the system:

1. **get_status()** - Current power, angles, sun position
2. **switch_mode(mode)** - Switch "Reactive" ↔ "Predictive"
3. **move_to(pan, tilt)** - Manual positioning
4. **explain_delta()** - A/B test results
5. **get_impact()** - Energy, cost, CO2 metrics
6. **get_safety_status()** - Servo health, temperature

## 📡 MQTT Topics

The agent **subscribes** to these topics:
- `helios/sensors/raw` - Sensor data (LDRs, INA219)
- `helios/status` - System status (mode, angles, sun position)
- `helios/ai/performance_delta` - A/B comparison data
- `helios/impact` - Environmental impact metrics
- `helios/safety` - Safety monitoring data

The agent **publishes** to these topics:
- `helios/command/mode` - Mode switching commands
- `helios/command/position` - Position commands

## 🏗️ Architecture

```
┌─────────────────┐
│   User Voice    │
└────────┬────────┘
         │
         v
┌──────────────────────────────────────┐
│  gemini-2.5-flash-native-audio-dialog│
│         (Audio In/Out)               │
└────────────┬─────────────────────────┘
             │
             v
┌──────────────────────────────────────┐
│      ADK Agent Tools                 │
│  • get_status()                      │
│  • switch_mode()                     │
│  • move_to()                         │
│  • explain_delta()                   │
│  • get_impact()                      │
│  • get_safety_status()               │
└────────────┬─────────────────────────┘
             │
             v
┌──────────────────────────────────────┐
│      MQTT Client (paho-mqtt)         │
│  Subscribe/Publish to topics         │
└────────────┬─────────────────────────┘
             │
             v
┌──────────────────────────────────────┐
│  Raspberry Pi MQTT Broker            │
│  (Mosquitto)                         │
└──────────────────────────────────────┘
             │
             v
┌──────────────────────────────────────┐
│  Arduino (Servos + Sensors)          │
└──────────────────────────────────────┘
```

## 🧪 Testing Without Hardware

Test the agent with mock data while the dashboard is running:

```bash
# Terminal 1: Run dashboard with mock data
cd /home/leo/code/helios/dashboard
python dashboard.py

# Terminal 2: Run the agent
cd /home/leo/code/helios/adk
source ../venv/bin/activate
adk web --port 8000 helios_agent
```

Open http://localhost:8000 and try voice commands!

## 🔧 Troubleshooting

**"Import could not be resolved" warnings:**
- Normal IDE warnings - venv is not detected by IDE
- Code runs fine when venv is activated

**"No data available yet":**
- Ensure MQTT broker is running
- Check services are publishing to topics
- Verify `MQTT_BROKER_HOST` in `.env`

**API Key errors:**
- Set `GOOGLE_GENAI_API_KEY` in `helios_agent/.env`
- Get key from https://aistudio.google.com/apikey
- Check API access is enabled

**Can't connect to MQTT:**
- If testing locally, use `MQTT_BROKER_HOST=localhost`
- For Pi, use Pi's IP address (e.g., `192.168.1.100`)
- Ensure Mosquitto broker is running

## 📂 Project Structure

```
adk/
├── venv/                    # Virtual environment
├── helios_agent/            # ADK agent
│   ├── agent.py            # Main agent with tools
│   ├── .env                # API keys (NOT in git)
│   └── __init__.py
└── README.md               # This file
```