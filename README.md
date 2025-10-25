# Helios AI - Voice-Controlled Solar Tracker

A voice-first, AI-powered solar tracking platform with real-time digital twin simulation.

## 🔐 Security Setup (IMPORTANT!)

**Your API keys are secured and will NOT be pushed to GitHub.**

### First Time Setup:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment configuration:**
   - Your `.env` file already contains your API keys
   - This file is ignored by git (check `.gitignore`)
   - **NEVER** commit the `.env` file

3. **For team members:**
   - Copy `.env.example` to `.env`
   - Add your own API keys
   - Update `MQTT_BROKER_HOST` with Raspberry Pi's IP address

### Verify Security:

```bash
# Check that .env is NOT tracked by git
git status

# .env should NOT appear in the output!
```

## 🚀 Quick Start

### Test Configuration:
```bash
python config/config.py
```

This will verify all settings are loaded correctly WITHOUT exposing secrets.

## 📡 System Architecture

- **Raspberry Pi:** MQTT broker + Arduino interface
- **MacBook Pro:** AI logic, dashboard, voice control
- **Arduino:** Hardware control (servos, sensors)

## 🔑 Required API Keys

1. **OpenWeatherMap** (Free): https://openweathermap.org/api
   - Already configured in your `.env`

2. **Porcupine Wake Word** (Free tier): https://console.picovoice.ai/
   - Add to `.env` when ready

3. **Google ADK** (Free): For voice agent
   - Add project ID to `.env` when ready

## 🛠️ Development

### Project Structure:
```
helios-ai/
├── .env                 # ← YOUR SECRETS (never commit!)
├── .env.example         # ← Template for team
├── .gitignore           # ← Protects .env
├── config/              # ← Configuration loader
├── services/            # ← MQTT, weather, sun calc
├── dashboard/           # ← Flask web dashboard
├── agents/              # ← AI logic & agents
└── mock_data/           # ← Testing data
```

## ⚠️ Security Reminders

- ✅ `.env` is in `.gitignore`
- ✅ API keys never appear in code
- ✅ Config validation prevents missing keys
- ✅ Safe string representation hides secrets
- ❌ NEVER run `git add .env`
- ❌ NEVER share `.env` file publicly
- ❌ NEVER log or print `OPENWEATHER_API_KEY`

## 🎯 Hackathon Day Checklist

- [ ] Update `MQTT_BROKER_HOST` with Pi's IP
- [ ] Update `WEATHER_LAT`/`WEATHER_LON` with venue location
- [ ] Test all services with `mock_data` mode
- [ ] Verify `.env` is NOT in git
- [ ] Test dashboard connection
- [ ] Test voice commands
- [ ] Have backup demo mode ready

## 📞 Usage Example

```python
from config.config import Config, Topics

# Load configuration (secrets loaded automatically)
print(Config.get_safe_config_string())  # Safe to display

# Use API key in code (but never log it!)
api_key = Config.OPENWEATHER_API_KEY

# Use MQTT topics
import paho.mqtt.client as mqtt
client = mqtt.Client()
client.connect(Config.MQTT_BROKER_HOST, Config.MQTT_BROKER_PORT)
client.subscribe(Topics.SENSORS_RAW)
```

## 🧪 Testing

```bash
# Test configuration loading
python config/config.py

# Test MQTT connection (when Pi is ready)
python tests/test_mqtt_connection.py

# Run dashboard in mock mode
MOCK_DATA_MODE=True python dashboard/dashboard.py
```

---

Built for Google ADK Hackathon 2024
