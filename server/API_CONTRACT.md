# Helios AI Backend API Contract

This document defines the complete API contract between the Flask backend and the React frontend.

**Base URL (Development):** `http://localhost:5000`
**Base URL (Production):** `http://YOUR_VULTR_IP:8080`

---

## REST API Endpoints

### 1. Health Check
Monitor server status and connectivity.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "mock_mode": true,
  "connected_clients": 2,
  "timestamp": 1234567890
}
```

---

### 2. Configuration
Get safe configuration values (no API keys exposed).

**Endpoint:** `GET /api/config`

**Response:**
```json
{
  "default_lat": 37.7749,
  "default_lon": -122.4194
}
```

---

### 3. Weather Proxy
Fetch weather data without exposing API key.

**Endpoint:** `GET /api/weather?lat={lat}&lon={lon}`

**Query Parameters:**
- `lat` (required): Latitude (-90 to 90)
- `lon` (required): Longitude (-180 to 180)

**Response:**
```json
{
  "source": "api",
  "data": {
    "location": "San Francisco",
    "coords": {"lat": 37.77, "lon": -122.41},
    "weather": "clear sky",
    "temp_c": 18.5,
    "humidity": 65,
    "wind_m_s": 3.2,
    "timestamp": 1234567890
  }
}
```

**Error Responses:**
- `400`: Invalid parameters
- `429`: Rate limit exceeded (30 requests/minute per IP)
- `502`: Upstream API unreachable
- `503`: Server configuration missing

---

### 4. Reverse Geocoding Proxy
Convert coordinates to city name.

**Endpoint:** `GET /api/geocode/reverse?lat={lat}&lon={lon}`

**Query Parameters:**
- `lat` (required): Latitude
- `lon` (required): Longitude

**Response:**
```json
{
  "source": "cache",
  "data": {
    "name": "San Francisco",
    "state": "California",
    "country": "US"
  }
}
```

---

### 5. Cloud Tiles Proxy
Get cloud coverage map tiles for Leaflet.js.

**Endpoint:** `GET /api/tiles/clouds/{z}/{x}/{y}.png`

**Path Parameters:**
- `z`: Zoom level (0-19)
- `x`: Tile X coordinate
- `y`: Tile Y coordinate

**Response:** PNG image with cloud overlay

**Headers:**
```
Content-Type: image/png
Cache-Control: public, max-age=600
```

---

## WebSocket Events (Socket.IO)

**Connection URL:** Same as base URL (Flask-SocketIO auto-detects)

### Connecting to WebSocket

```javascript
import { io } from 'socket.io-client';

const socket = io('http://localhost:5000', {
  transports: ['websocket'],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5
});
```

---

### Client → Server Events

#### Connect Event
```javascript
socket.on('connect', () => {
  console.log('Connected to Helios AI');
});
```

#### Request Data
```javascript
socket.emit('request_data', { topic: 'all' });
// Options: 'all', 'helios/sensors/raw', 'helios/status', etc.
```

---

### Server → Client Events

#### Connection Status
Sent immediately upon connection.

```javascript
socket.on('connection_status', (data) => {
  // data = {
  //   status: "connected",
  //   mock_mode: true,
  //   timestamp: 1234567890
  // }
});
```

---

#### Sensor Data (1Hz)
Real-time sensor readings from solar panel.

```javascript
socket.on('sensor_data', (data) => {
  // data = {
  //   ldr_top: 850,        // Light sensor top (0-1023)
  //   ldr_bottom: 720,     // Light sensor bottom
  //   ldr_left: 780,       // Light sensor left
  //   ldr_right: 810,      // Light sensor right
  //   voltage: 18.2,       // Volts
  //   current: 1.45,       // Amps
  //   power: 26.39,        // Watts
  //   timestamp: 1234567890
  // }
});
```

---

#### Status Data (1Hz)
System status and position information.

```javascript
socket.on('status_data', (data) => {
  // data = {
  //   mode: "predictive",       // tracking | predictive | manual
  //   panel_azimuth: 180,       // degrees (0-360)
  //   panel_elevation: 45,      // degrees (0-90)
  //   sun_azimuth: 182,         // degrees
  //   sun_elevation: 47,        // degrees
  //   cloud_cover: 15,          // percent (0-100)
  //   timestamp: 1234567890
  // }
});
```

---

#### Performance Delta (0.5Hz - every 2 seconds)
A/B comparison results from micro-dither sampling.

```javascript
socket.on('performance_delta', (data) => {
  // data = {
  //   position_a_power: 26.5,   // Watts (current position)
  //   position_b_power: 24.8,   // Watts (alternative position)
  //   delta_watts: 1.7,         // Power difference
  //   delta_percent: 6.85,      // Percentage improvement
  //   timestamp: 1234567890
  // }
});
```

---

#### Impact Data (0.5Hz - every 2 seconds)
Environmental impact metrics.

```javascript
socket.on('impact_data', (data) => {
  // data = {
  //   energy_kwh: 4.23,         // Total energy generated
  //   cost_saved_usd: 0.52,     // Money saved
  //   co2_avoided_kg: 2.96,     // CO2 emissions avoided
  //   timestamp: 1234567890
  // }
});
```

---

#### Safety Data (0.5Hz - every 2 seconds)
System safety monitoring.

```javascript
socket.on('safety_data', (data) => {
  // data = {
  //   servo_health: "healthy",  // healthy | degraded | failed
  //   temperature_c: 45.2,      // Celsius
  //   violations: [],           // Array of safety violation strings
  //   timestamp: 1234567890
  // }
});
```

---

## Environment Variables for React Client

### Development (.env.development)
```bash
VITE_API_URL=http://localhost:5000
```

### Production (.env.production)
```bash
VITE_API_URL=http://YOUR_VULTR_IP:8080
```

---

## CORS & Security

The backend is configured to accept requests from:
- `http://localhost:3000` (Create React App default)
- `http://localhost:5173` (Vite default)
- `http://localhost:80` (Production static server)
- `http://YOUR_VULTR_IP` (Production deployment)

If Loveable uses a different port, update `/server/.env`:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:XXXX
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:XXXX
```

---

## Mock Data Mode

The backend runs in **mock mode** by default for development (no hardware required).

Set in `/server/.env`:
```bash
MOCK_DATA_MODE=True
```

All data will be realistic simulations with time-based variations:
- Sensor values change based on simulated sun movement
- Cloud cover varies realistically
- Impact metrics accumulate over time
- Safety data simulates normal operating conditions

Perfect for frontend development without physical hardware!

---

## Example React Integration

### Fetch API Example
```typescript
// services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export const api = {
  async getHealth() {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
  },

  async getWeather(lat: number, lon: number) {
    const response = await fetch(
      `${API_BASE_URL}/api/weather?lat=${lat}&lon=${lon}`
    );
    if (!response.ok) throw new Error('Weather fetch failed');
    return response.json();
  }
};
```

### WebSocket Example
```typescript
// services/socket.ts
import { io } from 'socket.io-client';

const SOCKET_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export const socket = io(SOCKET_URL, {
  transports: ['websocket'],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5
});

socket.on('connect', () => console.log('Connected'));
socket.on('sensor_data', (data) => console.log('Sensors:', data));
socket.on('status_data', (data) => console.log('Status:', data));
```

---

## Testing the Backend

### Quick Test Checklist

1. **Start the server:**
   ```bash
   cd server
   python dashboard/dashboard.py
   ```

2. **Test health endpoint:**
   ```
   http://localhost:5000/health
   ```
   Should return: `{"status": "healthy", ...}`

3. **Test weather API:**
   ```
   http://localhost:5000/api/weather?lat=37.7749&lon=-122.4194
   ```

4. **Test WebSocket (browser console):**
   ```javascript
   const script = document.createElement('script');
   script.src = 'https://cdn.socket.io/4.5.4/socket.io.min.js';
   document.head.appendChild(script);

   setTimeout(() => {
     const socket = io('http://localhost:5000');
     socket.on('connect', () => console.log('✅ Connected'));
     socket.on('sensor_data', (data) => console.log('📊 Sensors:', data));
   }, 2000);
   ```

---

## Deployment Notes

### Vultr Production Setup

**Backend runs on port 8080:**
```bash
cd server
python dashboard/dashboard.py
# Runs on http://YOUR_IP:8080
```

**Frontend runs on port 80:**
```bash
cd client
npm run build
serve -s dist -l 80
# Runs on http://YOUR_IP
```

**Update production .env:**
```bash
# /server/.env
CORS_ORIGINS=http://YOUR_VULTR_IP,http://YOUR_VULTR_IP:80
ALLOWED_ORIGINS=http://YOUR_VULTR_IP,http://YOUR_VULTR_IP:80
DASHBOARD_PORT=8080
DEBUG_MODE=False
MOCK_DATA_MODE=False  # Set to True if no hardware
```

---

## Support

If you need endpoints added or modified, update this contract and notify the backend team.

All API keys are secured server-side - the frontend never sees them.

Rate limiting: 30 requests/minute per IP for weather endpoints.
Cache TTL: 15 minutes for weather data, 10 minutes for tiles.
