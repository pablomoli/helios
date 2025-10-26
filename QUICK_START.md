# Helios AI - Quick Start Guide

## 🚀 Starting Helios AI

There are **two services** you need to run:

### Method 1: Use the Start Script (Easiest!)

```bash
./start_helios.sh
```

This will start both services automatically!

### Method 2: Start Manually (Two Terminals)

**Terminal 1 - Dashboard:**
```bash
cd dashboard
../.venv/bin/python dashboard.py
```

**Terminal 2 - Gemini Voice Agent:**
```bash
cd adk
../.venv/bin/adk web --port 8001
```

---

## 🌐 Access the Interfaces

Once both services are running:

### 1. **Dashboard** - http://localhost:5000
- Shows solar tracker data (power, angles, etc.)
- Displays the **AI Voice Interface** with spectrogram visualization
- Shows when "Helios" wake word is detected

### 2. **Voice Agent** - http://localhost:8001
- Click the **microphone icon** to enable voice input
- Say: **"Helios, what's the status?"**
- The agent will respond with solar tracker information

---

## 🎤 Using Voice Commands

The wake word is **"Helios"** (not "computer" anymore!)

### Example Commands:

✅ **"Helios, what's the status?"**
- Gets current power, mode, and panel angles

✅ **"Helios, switch to predictive mode"**
- Changes tracking mode to astronomical calculations

✅ **"Helios, how much energy have we saved?"**
- Reports environmental impact metrics

✅ **"Helios, which mode is better?"**
- Compares Reactive vs Predictive performance

❌ **"What's the status?"** (no wake word)
- Agent will stay silent

---

## 🛑 Stopping Helios AI

### Method 1: Use the Stop Script
```bash
./stop_helios.sh
```

### Method 2: Manual Stop
```bash
pkill -f dashboard.py
pkill -f "adk web"
```

---

## 📊 What Each Service Does

### Dashboard (Port 5000)
- **Flask web app** that displays solar tracker data
- Shows real-time metrics, graphs, and safety monitoring
- Includes the **AI Voice Interface panel** with:
  - Wake word detection indicator
  - Live audio spectrogram
  - AI response display

### Voice Agent (Port 8001)
- **Gemini 2.5 Flash Live** voice model
- Listens for "Helios" wake word
- Processes voice queries about the solar tracker
- Can control the system (switch modes, move panels)

---

## 🔧 Troubleshooting

### Dashboard won't start
```bash
# Make sure you're using the virtual environment
cd dashboard
../.venv/bin/python dashboard.py
```

### Voice agent won't start
```bash
# Check if ADK is installed
../.venv/bin/pip show google-adk

# Install if missing
../.venv/bin/pip install google-adk deprecated
```

### Can't see the AI Voice panel on dashboard
- Make sure you're accessing http://localhost:5000
- Check browser console for JavaScript errors
- Refresh the page

### Voice not working
- Open http://localhost:8001 (not 5000)
- Click the microphone icon
- Allow browser microphone permissions
- Make sure to say "Helios" before your question

---

## 📝 View Logs

If you used the start script, logs are saved to `/tmp`:

```bash
# Dashboard logs
tail -f /tmp/helios_dashboard.log

# Voice agent logs
tail -f /tmp/helios_agent.log
```

---

## 🎯 Quick Test

1. Start both services: `./start_helios.sh`
2. Open dashboard: http://localhost:5000
3. Open voice agent: http://localhost:8001
4. Click the mic icon on the voice agent page
5. Say: **"Helios, what's the status?"**
6. Watch the dashboard AI Voice panel light up!
7. Hear the response from the agent

---

## ⚙️ Architecture

```
┌─────────────────────────────────────┐
│  Dashboard (Port 5000)              │
│  - Solar tracker metrics            │
│  - AI Voice Interface panel         │
│    • Wake word indicator            │
│    • Spectrogram visualization      │
│    • Response display               │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Voice Agent (Port 8001)            │
│  - Gemini 2.5 Flash Live            │
│  - Wake word detection: "Helios"    │
│  - Solar tracker control            │
│  - WebSocket → Serial Bridge        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Serial WebSocket Bridge (Port 5000)│
│  - Arduino USB communication        │
│  - Broadcasts sensor data           │
└─────────────────────────────────────┘
```

---

## 🔑 Environment Variables

Make sure your `.env` file has:

```bash
# Required for voice agent
GOOGLE_GENAI_API_KEY=your_api_key_here

# WebSocket server
WEBSOCKET_SERVER_URL=ws://localhost:5000

# Dashboard port
DASHBOARD_PORT=5000
```

---

That's it! You're ready to use Helios AI! 🎉
