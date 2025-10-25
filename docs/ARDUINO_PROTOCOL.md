# Arduino Serial Communication Protocol

## Overview

The Arduino communicates with the computer via USB serial using JSON messages. Each message is a single line terminated with `\n`.

## Arduino → Computer (Outgoing Data)

The Arduino sends JSON messages with a `type` field to identify the data category.

### 1. Sensor Data
Sent periodically (every 1-2 seconds) with real-time sensor readings.

```json
{
  "type": "sensors",
  "timestamp": 1666215482,
  "ldr_tl": 812,
  "ldr_tr": 750,
  "ldr_bl": 600,
  "ldr_br": 580,
  "panel_voltage_V": 5.0,
  "panel_current_mA": 150.0,
  "panel_power_mW": 750.0
}
```

**Fields:**
- `ldr_tl` - Top-left LDR sensor reading (0-1023)
- `ldr_tr` - Top-right LDR sensor reading (0-1023)
- `ldr_bl` - Bottom-left LDR sensor reading (0-1023)
- `ldr_br` - Bottom-right LDR sensor reading (0-1023)
- `panel_voltage_V` - Solar panel voltage in volts
- `panel_current_mA` - Solar panel current in milliamps
- `panel_power_mW` - Calculated power in milliwatts

### 2. Status Data
Sent when servo positions change or mode switches.

```json
{
  "type": "status",
  "timestamp": 1666215483,
  "mode": "Predictive",
  "pan_angle_deg": 90.0,
  "tilt_angle_deg": 45.0
}
```

**Fields:**
- `mode` - Current tracking mode: "Reactive" or "Predictive"
- `pan_angle_deg` - Current pan servo angle (0-180°)
- `tilt_angle_deg` - Current tilt servo angle (0-180°)

### 3. Energy Data
Sent periodically (every 10 seconds) with cumulative energy metrics.

```json
{
  "type": "energy",
  "timestamp": 1666215599,
  "energy_saved_kWh": 0.0012
}
```

**Fields:**
- `energy_saved_kWh` - Cumulative energy saved in kilowatt-hours

### 4. Safety Alerts (Optional)
Sent when Arduino detects a safety issue.

```json
{
  "type": "safety",
  "timestamp": 1666215603,
  "alert": true,
  "message": "Temperature high",
  "temperature_C": 82.5
}
```

**Fields:**
- `alert` - Boolean, true if there's a safety concern
- `message` - Human-readable alert message
- `temperature_C` - Current temperature in Celsius (if available)

---

## Computer → Arduino (Incoming Commands)

The computer sends JSON commands to control the Arduino.

### 1. Position Command
Move servos to specific angles.

```json
{
  "type": "position",
  "pan_angle_deg": 95.0,
  "tilt_angle_deg": 40.0
}
```

**Safety Constraints:**
- `pan_angle_deg` must be 0-180
- `tilt_angle_deg` must be 0-180
- Arduino should clamp values to safe range

### 2. Mode Command
Switch tracking mode.

```json
{
  "type": "mode",
  "mode": "Predictive"
}
```

**Valid modes:**
- `"Reactive"` - Use LDR sensors for tracking
- `"Predictive"` - Use computer-calculated sun position

---

## Example Arduino Sketch Structure

```cpp
void setup() {
  Serial.begin(9600);
  // Initialize sensors and servos
}

void loop() {
  // Read and send sensor data
  sendSensorData();

  // Check for incoming commands
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    processCommand(cmd);
  }

  delay(1000);  // 1 second loop
}

void sendSensorData() {
  StaticJsonDocument<256> doc;
  doc["type"] = "sensors";
  doc["timestamp"] = millis();
  doc["ldr_tl"] = analogRead(A0);
  doc["ldr_tr"] = analogRead(A1);
  // ... more fields

  serializeJson(doc, Serial);
  Serial.println();  // Newline terminator
}

void processCommand(String json) {
  StaticJsonDocument<256> doc;
  deserializeJson(doc, json);

  String type = doc["type"];
  if (type == "position") {
    float pan = doc["pan_angle_deg"];
    float tilt = doc["tilt_angle_deg"];
    moveServos(pan, tilt);
  }
  // ... more command types
}
```

---

## Serial Configuration

- **Baud Rate:** 9600
- **Data Format:** 8-N-1 (8 data bits, no parity, 1 stop bit)
- **Line Ending:** `\n` (newline)
- **Port:**
  - Linux: `/dev/ttyUSB0` or `/dev/ttyACM0`
  - Windows: `COM3`, `COM4`, etc.
  - macOS: `/dev/tty.usbserial-*` or `/dev/tty.usbmodem-*`

---

## Required Arduino Libraries

- **ArduinoJson** - For JSON parsing (install via Arduino Library Manager)
- **Servo** - For servo control (built-in)

```cpp
#include <ArduinoJson.h>
#include <Servo.h>
```

---

## Testing

Use the standalone serial bridge to test Arduino communication:

```bash
# Test without WebSocket (prints to console)
python services/serial_bridge.py

# Full system with WebSocket server
python services/serial_websocket_bridge.py
```

---

## Safety Notes

1. **Always validate incoming angles** on the Arduino side
2. **Clamp values** to safe ranges (0-180° for both axes)
3. **Add delays** between servo movements to prevent mechanical stress
4. **Monitor temperature** if possible (via external sensor)
5. **Implement emergency stop** if any sensor reads dangerous values
