# Arduino Integration - Agent-to-Agent System

## Overview

Your Helios dashboard now has **two Gemini agents** working together:

1. **Data Collection Agent** (gemini-2.5-flash) - Reads Arduino sensor data, parses it, updates dashboard
2. **Voice Chat Agent** (gemini-2.5-flash) - Answers questions using real-time Arduino data

```
Arduino (Serial USB) → Data Agent (Gemini 2.5 Flash) → Shared State
                                                            ↓
                                                       Dashboard
                                                            ↓
                                                       Voice Agent (Gemini 2.5 Flash)
```

## Files Created

1. **`services/arduino_agent.py`** - Arduino data collection agent with Gemini parsing
2. **Updated `dashboard/dashboard.py`** - Integrated Arduino agent + Voice agent access
3. **Updated `requirements.txt`** - Added `pyserial` and `google-generativeai`
4. **Updated `.env.example`** - Added Arduino configuration

## Setup Instructions

### 1. Install Dependencies

```bash
# In your venv
pip install pyserial google-generativeai
```

Or install all:
```bash
pip install -r requirements.txt
```

### 2. Configure Arduino Connection

Edit your `.env` file:

```env
# Enable Arduino
ARDUINO_ENABLED=true

# Serial port (check with 'ls /dev/ttyUSB*' or 'ls /dev/ttyACM*')
ARDUINO_PORT=/dev/ttyUSB0

# Baud rate (must match your Arduino code)
ARDUINO_BAUD_RATE=9600
```

### 3. Arduino Code Format

Your Arduino should send data via Serial. The Gemini agent will parse it intelligently.

**Example Arduino Output:**
```
Voltage: 12.5V, Current: 850mA, Power: 10625mW, Temp: 25.3C
```

or JSON format:
```json
{"voltage":12.5,"current":850,"power":10625,"temperature":25.3}
```

or any format - Gemini will parse it!

### 4. Test Arduino Agent Standalone

```bash
cd services
python arduino_agent.py
```

This will:
- List available serial ports
- Let you select your Arduino
- Start reading and parsing data
- Show parsed JSON output

### 5. Run Dashboard with Arduino

```bash
cd dashboard
python dashboard.py
```

You'll see:
```
[Arduino] Starting Arduino agent on /dev/ttyUSB0...
[Arduino] Arduino agent started successfully
[Arduino] Data updated: Power=10625mW, Temp=25.3°C
```

## How It Works

### Data Collection Agent

```python
# Reads from Arduino
raw_data = "Voltage: 12.5V, Current: 850mA, Power: 10625mW"

# Sends to Gemini for parsing
parsed = {
    "voltage": 12.5,
    "current": 850,
    "power": 10625,
    "temperature": null
}

# Updates shared state
arduino_current_data = parsed

# Broadcasts to dashboard
socketio.emit('arduino_data', parsed)
```

### Voice Agent Access

When you ask: **"What's the current power?"**

The voice agent system instruction includes:
```
CURRENT REAL-TIME DATA FROM ARDUINO:
- Voltage: 12.5 V
- Current: 850 mA
- Power: 10625 mW
- Temperature: 25.3°C
...
```

Voice agent responds: **"The current power is 10625 milliwatts."**

## Data Flow

```
1. Arduino sends: "V=12.5, I=850, P=10625"
2. Data Agent reads via Serial
3. Gemini parses → JSON
4. Updates arduino_current_data (shared state)
5. Broadcasts to dashboard (SocketIO)
6. Voice agent reads from shared state when asked
```

## Arduino Code Example

```cpp
void setup() {
  Serial.begin(9600);
}

void loop() {
  float voltage = analogRead(A0) * (5.0 / 1023.0);
  float current = analogRead(A1) * 10.0; // Example conversion
  float power = voltage * current;
  float temperature = readTemperature(); // Your sensor

  // Simple format - Gemini will parse it
  Serial.print("Voltage: ");
  Serial.print(voltage);
  Serial.print("V, Current: ");
  Serial.print(current);
  Serial.print("mA, Power: ");
  Serial.print(power);
  Serial.print("mW, Temp: ");
  Serial.print(temperature);
  Serial.println("C");

  delay(1000); // Send every second
}
```

## Configuration Options

### Update Frequency

Default: 1 second (1.0)

Change in `dashboard.py` line 750:
```python
update_interval=1.0  # Read every 1 second
```

### Gemini Model

Default: `gemini-2.5-flash`

Change in `dashboard.py` line 749:
```python
model_name='gemini-2.5-flash'  # or 'gemini-1.5-flash'
```

### Serial Settings

In `.env`:
```env
ARDUINO_PORT=/dev/ttyUSB0    # Your Arduino port
ARDUINO_BAUD_RATE=9600       # Must match Arduino Serial.begin()
```

## Troubleshooting

### "Failed to connect to Arduino"

**Check port:**
```bash
# Linux
ls /dev/ttyUSB* /dev/ttyACM*

# macOS
ls /dev/cu.*

# Windows
# Check Device Manager → Ports (COM & LPT)
```

**Permission denied (Linux):**
```bash
sudo usermod -a -G dialout $USER
# Logout and login
```

### "No data received"

1. Check Arduino is sending data:
   ```bash
   cat /dev/ttyUSB0  # Should see Arduino output
   ```

2. Check baud rate matches:
   - Arduino: `Serial.begin(9600)`
   - `.env`: `ARDUINO_BAUD_RATE=9600`

3. Check Arduino USB cable is data cable (not just power)

### "Parse failed"

The Gemini agent is very flexible! It can parse:
- Plain text: `"V: 12.5, I: 850"`
- CSV: `"12.5,850,10625,25.3"`
- JSON: `{"voltage":12.5,"current":850}`
- Any format!

If parsing fails repeatedly, check:
- Arduino is sending complete lines (ends with `\n`)
- Data is readable text (not binary)

### Voice agent says "0" for all values

Arduino agent not running or not receiving data. Check:
```bash
# In dashboard terminal, look for:
[Arduino] Data updated: Power=10625mW, Temp=25.3°C
```

## Testing Without Arduino

Leave `ARDUINO_ENABLED=false` - dashboard uses mock data.

## Data Fields

The agent expects these fields (all optional):
- `voltage` - Panel voltage (V)
- `current` - Current (mA)
- `power` - Power output (mW)
- `temperature` - System temp (°C)
- `azimuth` - Panel azimuth angle (degrees)
- `elevation` - Panel elevation angle (degrees)
- `cloud_coverage` - Cloud coverage (0-100%)
- `timestamp` - Data timestamp

Missing fields are set to `null`.

## Advanced: Custom Parsing

Edit `arduino_agent.py` line 95 to customize the Gemini prompt for your specific Arduino format.

## Agent Models

- **Data Collection**: `gemini-2.5-flash` - Fast, accurate parsing, structured output
- **Voice Chat**: `gemini-2.5-flash` - Conversational, concise answers

Both agents share the same API key (`GEMINI_API_KEY`).

---

**You're all set!** Connect your Arduino, enable it in `.env`, and restart the dashboard.

The voice agent will now answer with **real-time Arduino data**! 🎉
