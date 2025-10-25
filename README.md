# Helios AI - Voice-Controlled Solar Tracker

A voice-first, AI-powered solar tracking platform with real-time digital twin simulation and live analytics dashboard.

**✨ Features:**
- 🎨 Apple-inspired glassmorphism UI with smooth animations
- 🗺️ Live cloud coverage map with your location
- 📊 Real-time power generation analytics
- 📈 A/B comparison of tracking strategies (Digital Twin)
- 🌱 Environmental impact tracking (CO2, cost savings)
- 🔒 Secure API key handling (no keys exposed to frontend)

---

## 📋 Prerequisites (Start Here!)

Before you begin, make sure you have these installed:

### 1. **Python 3.8 or higher**
Check if you have Python installed:
```bash
python --version
```

**Don't have Python?** Download it here:
- **Windows/Mac:** https://www.python.org/downloads/
- **Linux:** `sudo apt-get install python3`

### 2. **Git** (for cloning the repository)
Check if you have Git installed:
```bash
git --version
```

**Don't have Git?** Download it here: https://git-scm.com/downloads

---

## 🚀 Quick Start Guide (Step-by-Step)

### Step 1: Clone the Repository

Open your terminal/command prompt and run:

```bash
# Clone the repo
git clone <your-repo-url>

# Navigate into the project folder
cd hack
```

### Step 2: Install Python Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

**Note:** On some systems, you might need to use `pip3` instead of `pip`:
```bash
pip3 install -r requirements.txt
```

**Having issues?** Try:
```bash
python -m pip install -r requirements.txt
```

### Step 3: Set Up Your Environment Variables

1. **Copy the example environment file:**
   ```bash
   # On Windows (Command Prompt)
   copy .env.example .env

   # On Windows (PowerShell)
   Copy-Item .env.example .env

   # On Mac/Linux
   cp .env.example .env
   ```

2. **Get a FREE OpenWeatherMap API Key:**
   - Go to https://openweathermap.org/api
   - Sign up for a free account
   - Copy your API key

3. **Edit the `.env` file:**
   - Open `.env` in any text editor (Notepad, VS Code, etc.)
   - Replace `your_api_key_here` with your actual OpenWeatherMap API key
   - Save the file

   Example `.env` file:
   ```env
   OPENWEATHER_API_KEY=abc123youractualkey456
   WEATHER_LAT=37.7749
   WEATHER_LON=-122.4194
   MOCK_DATA_MODE=True
   DEBUG_MODE=True
   ```

### Step 4: Test Your Configuration

Make sure everything is set up correctly:

```bash
python config/config.py
```

You should see output like:
```
[OK] Configuration loaded successfully!
Helios AI Configuration:
  MQTT Broker: localhost:1883
  Location: (37.7749, -122.4194)
  Dashboard Port: 5000
  Mock Data Mode: True
  Debug Mode: True
  OpenWeather API: Configured [OK]
```

### Step 5: Run the Dashboard! 🎉

Start the dashboard server:

```bash
python dashboard/dashboard.py
```

You should see:
```
============================================================
Helios AI Dashboard Starting...
============================================================
Mock Data Mode: True
Dashboard URL: http://localhost:5000
============================================================
[Dashboard] Starting data broadcast thread...
 * Running on http://0.0.0.0:5000
```

### Step 6: Open in Your Browser

1. Open your web browser
2. Go to: **http://localhost:5000**
3. Allow location access when prompted (to show your city name on the map)
4. Watch the dashboard come alive with real-time data! ✨

---

## 🎨 What You'll See

The dashboard includes **6 live panels**:

1. **🗺️ Live Cloud Coverage Map** - Shows cloud coverage over your location
2. **📊 Real-Time Analytics** - Current power, energy today, system mode
3. **📈 A/B Comparison Graph** - Digital twin performance comparison
4. **🌱 Environmental Impact** - Energy saved, cost savings, CO2 avoided
5. **🔒 Safety Monitor** - System health and safety status
6. **🎤 Voice Command Log** - Voice interaction history (coming soon)

---

## 🔧 Troubleshooting

### Problem: "pip: command not found"
**Solution:** Python might not be in your PATH. Try:
```bash
python -m pip install -r requirements.txt
```

### Problem: "ModuleNotFoundError"
**Solution:** Make sure you installed dependencies:
```bash
pip install -r requirements.txt
```

### Problem: "Address already in use" (Port 5000 busy)
**Solution:** Another app is using port 5000. Change the port in `.env`:
```env
DASHBOARD_PORT=5001
```

### Problem: Dashboard shows "--" for all values
**Solution:** Wait 2-3 seconds for mock data to start streaming. Refresh the page if needed.

### Problem: Location shows coordinates instead of city name
**Solution:**
1. Make sure you allowed location access in your browser
2. Check that your OpenWeatherMap API key is valid
3. Check browser console (F12) for any error messages

### Problem: "Config validation failed"
**Solution:** Your `.env` file is missing or has errors. Make sure:
1. The `.env` file exists in the project root
2. `OPENWEATHER_API_KEY` is set to a valid key
3. No extra spaces around the `=` sign

---

## 🛠️ Project Structure

```
hack/
├── .env                   # YOUR API KEYS (never commit!)
├── .env.example           # Template for team members
├── .gitignore             # Protects .env from being committed
├── requirements.txt       # Python dependencies
├── config/
│   ├── config.py          # Configuration loader
│   └── __init__.py
├── services/
│   ├── weather_service.py # OpenWeatherMap integration
│   ├── mqtt_client.py     # MQTT client wrapper
│   └── __init__.py
├── mock_data/
│   ├── data_generator.py  # Realistic mock data for testing
│   └── __init__.py
└── dashboard/
    ├── dashboard.py       # Flask backend (START HERE!)
    ├── templates/
    │   └── index.html     # Main dashboard HTML
    └── static/
        ├── css/
        │   └── main.css   # All styling
        └── js/
            ├── main.js
            └── components/ # Modular JS components
```

---

## 🔐 Security Best Practices

**IMPORTANT:** Your API keys are protected!

- ✅ `.env` file is in `.gitignore` (won't be committed)
- ✅ API keys stay on backend (never sent to browser)
- ✅ Backend proxy endpoints keep keys secure
- ❌ **NEVER** run `git add .env`
- ❌ **NEVER** commit or share your `.env` file
- ❌ **NEVER** log or print your API keys

**Verify your .env is safe:**
```bash
git status
# The .env file should NOT appear in the output!
```

---

## 📡 How It Works

### Current Demo Mode (No Hardware Required!)
- **Frontend:** Modern web dashboard with real-time updates
- **Backend:** Flask server with WebSocket streaming
- **Mock Data:** Realistic simulated sensor data for testing

### Full System (Hardware Integration)
When you're ready to connect hardware:

1. **Raspberry Pi** - Runs MQTT broker, connects to Arduino
2. **Arduino** - Controls servos and reads sensors
3. **Laptop/Computer** - Runs dashboard and AI logic
4. **Communication** - All components talk via MQTT messages

---

## 🧪 Advanced Usage

### Running Without Mock Data
When you have real hardware connected:

1. Update `.env`:
   ```env
   MOCK_DATA_MODE=False
   MQTT_BROKER_HOST=192.168.1.XXX  # Your Raspberry Pi's IP
   ```

2. Make sure Mosquitto MQTT broker is running on the Pi

3. Start the dashboard:
   ```bash
   python dashboard/dashboard.py
   ```

### Testing Individual Components

**Test weather service:**
```bash
python services/weather_service.py
```

**Test MQTT client (requires broker running):**
```bash
python services/mqtt_client.py
```

**Test mock data generator:**
```bash
python mock_data/data_generator.py
```

### Customizing Your Location

Edit `.env` to set your coordinates:
```env
WEATHER_LAT=40.7128   # New York City latitude
WEATHER_LON=-74.0060  # New York City longitude
```

---

## 🎯 Demo Day Checklist

Before your presentation:

- [ ] Test dashboard in mock mode
- [ ] Verify your OpenWeatherMap API key works
- [ ] Check that location shows your city name
- [ ] Watch the animated background for 30 seconds (should be smooth)
- [ ] Test on the presentation computer
- [ ] Have a backup plan (screenshots/video)
- [ ] Close unnecessary browser tabs
- [ ] Test fullscreen mode (F11)

---

## 🤝 Contributing

This is a hackathon project! If you're a team member:

1. Clone the repo
2. Create your own `.env` file (copy from `.env.example`)
3. Add your own OpenWeatherMap API key
4. Make your changes
5. Commit (`.env` will be automatically ignored)
6. Push to GitHub

---

## 📚 Technologies Used

- **Backend:** Python, Flask, Flask-SocketIO
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Real-time:** WebSockets for live data streaming
- **Maps:** Leaflet.js with OpenWeatherMap tiles
- **Charts:** Chart.js for performance graphs
- **Design:** Apple-inspired glassmorphism, smooth animations

**No build step needed!** Just refresh the browser to see changes.

---

## 📄 License

Built for Google ADK Hackathon 2024

---

## 💡 Need Help?

**Common Issues:**
- Check the Troubleshooting section above
- Look for error messages in the terminal
- Press F12 in your browser to see console logs
- Make sure all dependencies are installed

**Still stuck?**
1. Verify Python version: `python --version` (should be 3.8+)
2. Verify dependencies: `pip list` (should show flask, requests, etc.)
3. Check your `.env` file exists and has the API key
4. Try restarting the dashboard server

---

**🎉 You're all set! Enjoy your Helios AI dashboard!**
