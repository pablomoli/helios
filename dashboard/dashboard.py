"""
Flask Dashboard with WebSocket support for Helios AI
Serves the web interface and streams real-time data
Includes Gemini Live API voice chat integration
"""
from flask import Flask, render_template, request, jsonify, abort
from flask_socketio import SocketIO, emit
from flask_sock import Sock
import time
import sys
from pathlib import Path
import os
from threading import Thread, Lock
import requests
from cachetools import TTLCache, LRUCache
import websockets
import ssl
import certifi
import base64
import json
import asyncio
import queue

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config, Topics
from mock_data.data_generator import MockDataGenerator
from services.arduino_agent import ArduinoDataAgent

app = Flask(__name__)

# SECRET_KEY handling: require environment variable in production; allow a
# development fallback only when DEBUG_MODE is enabled. Fail loudly otherwise.
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    if Config.DEBUG_MODE:
        # In debug mode use a clearly insecure fallback but log it so devs notice
        print("[WARNING] SECRET_KEY not set; using insecure development fallback. Do not use in production.")
        secret_key = 'helios_dev_insecure_secret'
    else:
        raise RuntimeError('SECRET_KEY environment variable not set. Aborting startup for security reasons.')

app.config['SECRET_KEY'] = secret_key

# Restrict allowed origins for Socket.IO. Read from environment variable
# ALLOWED_ORIGINS as comma-separated list. In production this must be set.
allowed_origins_env = os.environ.get('ALLOWED_ORIGINS', '')
if allowed_origins_env:
    cors_allowed_origins = [o.strip() for o in allowed_origins_env.split(',') if o.strip()]
else:
    # If not set, make a safe default for development only.
    if Config.DEBUG_MODE:
        cors_allowed_origins = [
            f'http://localhost:{Config.DASHBOARD_PORT}',
            'http://localhost:3000'
        ]
        print(f"[INFO] ALLOWED_ORIGINS not set; using development defaults: {cors_allowed_origins}")
    else:
        raise RuntimeError('ALLOWED_ORIGINS environment variable must be set in production to restrict Socket.IO origins.')

socketio = SocketIO(app, cors_allowed_origins=cors_allowed_origins)
sock = Sock(app)

# Mock data generator
mock_generator = MockDataGenerator()

# Gemini Voice Chat Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
GEMINI_MODEL = "models/gemini-2.0-flash-exp"
GEMINI_WS_URL = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={GEMINI_API_KEY}" if GEMINI_API_KEY else None

# System instruction for Helios AI voice assistant (with real-time data)
def get_voice_instruction_with_data():
    """Generate system instruction with current Arduino data"""
    with arduino_data_lock:
        data = arduino_current_data.copy()

    return {
        "parts": [{
            "text": f"""You are Helios, a concise AI assistant for a solar panel dashboard.

CURRENT REAL-TIME DATA FROM ARDUINO:
- Voltage: {data['voltage']} V
- Current: {data['current']} mA
- Power: {data['power']} mW
- Temperature: {data['temperature']}°C
- Panel Azimuth: {data['azimuth']}°
- Panel Elevation: {data['elevation']}°
- Cloud Coverage: {data['cloud_coverage']}%

CRITICAL RULES:
- Keep answers to 1-2 sentences MAXIMUM
- Use the EXACT real-time values shown above when asked about current data
- Answer ONLY what was asked - don't elaborate
- Never ask follow-up questions unless unclear
- Be direct and factual
- When greeted, say "Hello! I can tell you about your solar system's current performance" """
        }]
    }

# Global state
dashboard_state = {
    "mock_mode": Config.MOCK_DATA_MODE,
    "connected_clients": 0
}

# Arduino real-time data (shared between Arduino agent and voice agent)
arduino_data_lock = Lock()
arduino_current_data = {
    "voltage": 0,
    "current": 0,
    "power": 0,
    "temperature": 0,
    "azimuth": 0,
    "elevation": 0,
    "cloud_coverage": 0,
    "timestamp": None,
    "last_update": 0
}

# Arduino agent instance (initialized on startup)
arduino_agent = None

# Lock to guard connected_clients increments/decrements
connected_clients_lock = Lock()

# Lock to guard weather_cache and rate_limiter accesses
cache_lock = Lock()

# Bounded TTL cache for weather responses with automatic expiration
# maxsize=500 entries, TTL from config (default 900s = 15 min)
weather_cache = TTLCache(maxsize=500, ttl=Config.WEATHER_CACHE_TTL)

# Bounded LRU cache for rate limiter per-IP: { ip: (count, window_start) }
# maxsize=1000 IPs to prevent unbounded growth
rate_limiter = LRUCache(maxsize=1000)

RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 30     # max requests per window per IP


@app.route('/')
def index():
    """Serve the main dashboard page"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    # Read connected_clients under lock to avoid race conditions
    with connected_clients_lock:
        clients = dashboard_state["connected_clients"]

    return {
        "status": "healthy",
        "mock_mode": dashboard_state["mock_mode"],
        "connected_clients": clients,
        "timestamp": int(time.time())
    }


@app.route('/api/config')
def get_config():
    """Provide safe configuration to frontend"""
    # Do NOT expose API keys to the frontend. Return only non-sensitive defaults.
    return {
        "default_lat": Config.WEATHER_LAT,
        "default_lon": Config.WEATHER_LON
    }


@app.route('/api/weather')
def proxy_weather():
    """Proxy endpoint to fetch weather from OpenWeatherMap without exposing the API key.

    Accepts either lat & lon (preferred) or city as query params.
    Implements basic input validation, per-IP rate limiting, and a simple in-memory cache.
    """
    # Rate limiting per client IP
    client_ip = request.remote_addr or 'unknown'
    now = int(time.time())
    window = RATE_LIMIT_WINDOW

    with cache_lock:
        entry = rate_limiter.get(client_ip)
        if entry:
            count, start = entry
            if now - start < window:
                if count >= RATE_LIMIT_MAX:
                    return jsonify({"error": "rate_limit_exceeded"}), 429
                else:
                    rate_limiter[client_ip] = (count + 1, start)
            else:
                rate_limiter[client_ip] = (1, now)
        else:
            rate_limiter[client_ip] = (1, now)

    # Validate and parse inputs
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    city = request.args.get('city')

    if city:
        city = city.strip()
        if len(city) == 0 or len(city) > 100:
            return jsonify({"error": "invalid_city"}), 400
        cache_key = f"city:{city.lower()}"
        params = {"q": city}
    elif lat and lon:
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except ValueError:
            return jsonify({"error": "invalid_latlon"}), 400

        if not (-90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0):
            return jsonify({"error": "latlon_out_of_range"}), 400

        cache_key = f"ll:{lat_f:.6f},{lon_f:.6f}"
        params = {"lat": lat_f, "lon": lon_f}
    else:
        return jsonify({"error": "missing_parameters"}), 400

    # Check cache (TTLCache handles expiration automatically)
    with cache_lock:
        cached = weather_cache.get(cache_key)
    
    if cached:
        # TTLCache already validated TTL, so this is fresh
        return jsonify({"source": "cache", "data": cached})

    # Ensure API key exists
    if not Config.OPENWEATHER_API_KEY:
        return jsonify({"error": "server_configuration_missing"}), 503

    # Call OpenWeatherMap (server-side)
    owm_url = 'https://api.openweathermap.org/data/2.5/weather'
    query = {**params, 'appid': Config.OPENWEATHER_API_KEY, 'units': 'metric'}

    try:
        resp = requests.get(owm_url, params=query, timeout=5)
    except requests.RequestException:
        return jsonify({"error": "upstream_unreachable"}), 502

    if resp.status_code != 200:
        return jsonify({"error": "upstream_error", "status": resp.status_code}), resp.status_code

    payload = resp.json()

    # Reduce payload to only what's needed
    reduced = {
        'location': payload.get('name'),
        'coords': payload.get('coord'),
        'weather': payload.get('weather')[0].get('description') if payload.get('weather') else None,
        'temp_c': payload.get('main', {}).get('temp'),
        'humidity': payload.get('main', {}).get('humidity'),
        'wind_m_s': payload.get('wind', {}).get('speed'),
        'timestamp': payload.get('dt')
    }

    # Store in cache (TTLCache handles expiration automatically)
    with cache_lock:
        weather_cache[cache_key] = reduced

    return jsonify({"source": "api", "data": reduced})


@app.route('/api/tiles/clouds/<int:z>/<int:x>/<int:y>.png')
def proxy_cloud_tiles(z, x, y):
    """Proxy endpoint for OpenWeatherMap cloud tile images.

    Fetches cloud coverage tiles server-side to avoid exposing API key to frontend.
    Tiles follow standard slippy map format: zoom/x/y
    """
    # Validate tile coordinates (reasonable bounds)
    if not (0 <= z <= 19 and 0 <= x < 2**z and 0 <= y < 2**z):
        abort(400)

    # Ensure API key exists
    if not Config.OPENWEATHER_API_KEY:
        abort(503)

    # Fetch tile from OpenWeatherMap
    tile_url = f'https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png'
    params = {'appid': Config.OPENWEATHER_API_KEY}

    try:
        resp = requests.get(tile_url, params=params, timeout=10)
    except requests.RequestException:
        abort(502)

    if resp.status_code != 200:
        abort(resp.status_code)

    # Return the tile image with appropriate headers
    return resp.content, 200, {
        'Content-Type': 'image/png',
        'Cache-Control': 'public, max-age=600'  # Cache tiles for 10 minutes
    }


@app.route('/api/geocode/reverse')
def proxy_reverse_geocode():
    """Proxy endpoint for reverse geocoding (coordinates to city name).

    Converts lat/lon to city name without exposing API key to frontend.
    """
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({"error": "missing_parameters"}), 400

    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except ValueError:
        return jsonify({"error": "invalid_latlon"}), 400

    if not (-90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0):
        return jsonify({"error": "latlon_out_of_range"}), 400

    # Check cache (TTLCache handles expiration automatically)
    cache_key = f"geocode:{lat_f:.4f},{lon_f:.4f}"
    with cache_lock:
        cached = weather_cache.get(cache_key)
    
    if cached:
        return jsonify({"source": "cache", "data": cached})

    # Ensure API key exists
    if not Config.OPENWEATHER_API_KEY:
        return jsonify({"error": "server_configuration_missing"}), 503

    # Call OpenWeatherMap Geocoding API
    geocode_url = 'https://api.openweathermap.org/geo/1.0/reverse'
    params = {
        'lat': lat_f,
        'lon': lon_f,
        'limit': 1,
        'appid': Config.OPENWEATHER_API_KEY
    }

    try:
        resp = requests.get(geocode_url, params=params, timeout=5)
    except requests.RequestException:
        return jsonify({"error": "upstream_unreachable"}), 502

    if resp.status_code != 200:
        return jsonify({"error": "upstream_error", "status": resp.status_code}), resp.status_code

    payload = resp.json()

    if payload and len(payload) > 0:
        location = payload[0]
        result = {
            'name': location.get('name'),
            'state': location.get('state'),
            'country': location.get('country')
        }
    else:
        result = None

    # Store in cache (TTLCache handles expiration automatically)
    with cache_lock:
        weather_cache[cache_key] = result

    return jsonify({"source": "api", "data": result})


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    # Update connected client count atomically
    with connected_clients_lock:
        dashboard_state["connected_clients"] += 1
        current = dashboard_state["connected_clients"]

    print(f"[Dashboard] Client connected (total: {current})")

    # Send initial connection confirmation
    emit('connection_status', {
        "status": "connected",
        "mock_mode": dashboard_state["mock_mode"],
        "timestamp": int(time.time())
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    with connected_clients_lock:
        # Avoid negative counts in case of unexpected disconnect races
        dashboard_state["connected_clients"] = max(0, dashboard_state["connected_clients"] - 1)
        current = dashboard_state["connected_clients"]

    print(f"[Dashboard] Client disconnected (total: {current})")


@socketio.on('request_data')
def handle_data_request(data):
    """Handle manual data request from client"""
    topic = data.get('topic', 'all')

    if topic == 'all' or topic == Topics.SENSORS_RAW:
        emit('sensor_data', mock_generator.get_sensor_data())

    if topic == 'all' or topic == Topics.STATUS:
        emit('status_data', mock_generator.get_status())

    if topic == 'all' or topic == Topics.AI_PERFORMANCE_DELTA:
        emit('performance_delta', mock_generator.get_performance_delta())

    if topic == 'all' or topic == Topics.IMPACT:
        emit('impact_data', mock_generator.get_impact_data())

    if topic == 'all' or topic == Topics.SAFETY:
        emit('safety_data', mock_generator.get_safety_data())


def broadcast_data():
    """Background thread to broadcast data at regular intervals"""
    print("[Dashboard] Starting data broadcast thread...")

    while True:
        time.sleep(1)  # Send updates every second
        # Read connected_clients under lock
        with connected_clients_lock:
            clients = dashboard_state["connected_clients"]

        if clients > 0:
            # Broadcast all data types
            socketio.emit('sensor_data', mock_generator.get_sensor_data())
            socketio.emit('status_data', mock_generator.get_status())

            # Send these less frequently
            if int(time.time()) % 2 == 0:  # Every 2 seconds
                socketio.emit('performance_delta', mock_generator.get_performance_delta())
                socketio.emit('impact_data', mock_generator.get_impact_data())
                socketio.emit('safety_data', mock_generator.get_safety_data())


def start_broadcast_thread():
    """Start the background data broadcast thread"""
    thread = Thread(target=broadcast_data, daemon=True)
    thread.start()


# ============================================================================
# GEMINI VOICE CHAT INTEGRATION
# ============================================================================

class GeminiVoiceConnection:
    """Manages WebSocket connection to Gemini Live API for voice chat"""

    def __init__(self, client_ws):
        self.client_ws = client_ws
        self.gemini_ws = None
        self.client_to_gemini_queue = queue.Queue()
        self.running = False
        self.loop = None  # Store event loop to reuse

    def connect_to_gemini(self):
        """Establish WebSocket connection to Gemini Live API"""
        if not GEMINI_API_KEY or not GEMINI_WS_URL:
            print("[Gemini] API key not configured")
            return False

        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            # Create and store event loop
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.gemini_ws = self.loop.run_until_complete(
                websockets.connect(GEMINI_WS_URL, ssl=ssl_context)
            )
            print("[Gemini] WebSocket connected")
            return True
        except Exception as e:
            print(f"[Gemini] Connection error: {e}")
            return False

    def send_setup_message(self):
        """Send initial setup configuration to Gemini"""
        try:
            setup_msg = {
                "setup": {
                    "model": GEMINI_MODEL,
                    "generation_config": {
                        "response_modalities": ["AUDIO"],
                        "speech_config": {
                            "voice_config": {
                                "prebuilt_voice_config": {
                                    "voice_name": "Puck"
                                }
                            }
                        }
                    },
                    "system_instruction": get_voice_instruction_with_data()
                }
            }

            # Reuse the same event loop
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.gemini_ws.send(json.dumps(setup_msg)))
            print("[Gemini] Setup message sent")

            response = self.loop.run_until_complete(self.gemini_ws.recv())
            response_data = json.loads(response)

            if "setupComplete" in response_data:
                print("[Gemini] Setup complete")

                # Send initial prompt to start conversation
                initial_msg = {
                    "client_content": {
                        "turns": [{
                            "role": "user",
                            "parts": [{"text": "Hello! Introduce yourself briefly as Helios, the solar dashboard AI assistant."}]
                        }],
                        "turn_complete": True
                    }
                }
                self.loop.run_until_complete(self.gemini_ws.send(json.dumps(initial_msg)))
                print("[Gemini] Initial prompt sent")
                return True
            else:
                print(f"[Gemini] Setup failed: {response_data}")
                return False

        except Exception as e:
            print(f"[Gemini] Setup error: {e}")
            return False

    def client_to_gemini_worker(self):
        """Thread: Forward audio from client to Gemini"""
        print("[Worker] Client->Gemini thread started")

        try:
            while self.running:
                try:
                    audio_data = self.client_to_gemini_queue.get(timeout=0.1)
                    audio_b64 = base64.b64encode(audio_data).decode('utf-8')

                    message = {
                        "realtime_input": {
                            "media_chunks": [{
                                "mime_type": "audio/pcm;rate=16000",
                                "data": audio_b64
                            }]
                        }
                    }

                    # Use asyncio.run_coroutine_threadsafe for thread-safe execution
                    future = asyncio.run_coroutine_threadsafe(
                        self.gemini_ws.send(json.dumps(message)),
                        self.loop
                    )
                    future.result(timeout=5)  # Wait up to 5 seconds

                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"[Worker] Client->Gemini error: {e}")
                    break

        finally:
            print("[Worker] Client->Gemini thread stopped")

    def gemini_to_client_worker(self):
        """Thread: Forward audio from Gemini to client"""
        print("[Worker] Gemini->Client thread started")

        try:
            while self.running:
                try:
                    # Use asyncio.run_coroutine_threadsafe for thread-safe execution
                    future = asyncio.run_coroutine_threadsafe(
                        asyncio.wait_for(self.gemini_ws.recv(), timeout=0.1),
                        self.loop
                    )
                    message = future.result(timeout=5)

                    data = json.loads(message)

                    if "serverContent" in data:
                        server_content = data["serverContent"]

                        if "modelTurn" in server_content:
                            parts = server_content["modelTurn"].get("parts", [])

                            for part in parts:
                                if "inlineData" in part:
                                    audio_b64 = part["inlineData"].get("data", "")

                                    if audio_b64:
                                        audio_bytes = base64.b64decode(audio_b64)
                                        try:
                                            self.client_ws.send(audio_bytes)
                                        except Exception as e:
                                            print(f"[Worker] Send to client error: {e}")
                                            self.running = False
                                            break

                        if server_content.get("turnComplete"):
                            print("[Gemini] Turn complete")

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"[Worker] Gemini->Client error: {e}")
                    break

        finally:
            print("[Worker] Gemini->Client thread stopped")

    def run_event_loop(self):
        """Run the event loop in a separate thread"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def start(self):
        """Start the bidirectional streaming"""
        self.running = True

        # Start event loop in its own thread
        loop_thread = Thread(target=self.run_event_loop, daemon=True)
        loop_thread.start()

        client_thread = Thread(target=self.client_to_gemini_worker, daemon=True)
        gemini_thread = Thread(target=self.gemini_to_client_worker, daemon=True)

        client_thread.start()
        gemini_thread.start()

        client_thread.join()
        gemini_thread.join()

        # Stop the event loop
        self.loop.call_soon_threadsafe(self.loop.stop)

    def stop(self):
        """Stop the streaming and cleanup"""
        self.running = False
        try:
            if self.loop and self.gemini_ws:
                # Schedule close on the event loop
                future = asyncio.run_coroutine_threadsafe(
                    self.gemini_ws.close(),
                    self.loop
                )
                future.result(timeout=2)
                print("[Gemini] WebSocket closed")

                # Stop the event loop
                self.loop.call_soon_threadsafe(self.loop.stop)
        except Exception as e:
            print(f"[Gemini] Stop error: {e}")


@sock.route('/ws/gemini-voice')
def websocket_gemini_voice(ws):
    """WebSocket endpoint for Gemini voice chat"""
    print(f"[Gemini Voice] Client connected from {request.remote_addr}")

    if not GEMINI_API_KEY:
        ws.send(json.dumps({"error": "GEMINI_API_KEY not configured"}))
        return

    connection = GeminiVoiceConnection(ws)

    if not connection.connect_to_gemini():
        ws.send(json.dumps({"error": "Failed to connect to Gemini"}))
        return

    if not connection.send_setup_message():
        ws.send(json.dumps({"error": "Gemini setup failed"}))
        return

    ws.send(json.dumps({"status": "ready"}))

    worker_thread = Thread(target=connection.start, daemon=True)
    worker_thread.start()

    try:
        while True:
            data = ws.receive()

            if data is None:
                print("[Gemini Voice] Client disconnected")
                break

            if isinstance(data, bytes):
                connection.client_to_gemini_queue.put(data)

            elif isinstance(data, str):
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        ws.send(json.dumps({"type": "pong"}))
                except:
                    pass

    except Exception as e:
        print(f"[Gemini Voice] Error: {e}")
    finally:
        connection.stop()
        print("[Gemini Voice] Connection closed")


# ============================================================================
# ARDUINO DATA INTEGRATION
# ============================================================================

def on_arduino_data_update(data: dict):
    """Callback when Arduino agent receives new data"""
    global arduino_current_data

    with arduino_data_lock:
        # Update shared state
        arduino_current_data.update(data)
        arduino_current_data['last_update'] = time.time()

    # Broadcast to dashboard via SocketIO
    socketio.emit('arduino_data', data)

    print(f"[Arduino] Data updated: Power={data.get('power', 0)}mW, Temp={data.get('temperature', 0)}°C")


def start_arduino_agent():
    """Initialize and start the Arduino data collection agent"""
    global arduino_agent

    # Check if Arduino mode is enabled
    arduino_enabled = os.getenv('ARDUINO_ENABLED', 'false').lower() == 'true'
    arduino_port = os.getenv('ARDUINO_PORT', '/dev/ttyUSB0')
    arduino_baud = int(os.getenv('ARDUINO_BAUD_RATE', '9600'))

    if not arduino_enabled:
        print("[Arduino] Arduino mode disabled (set ARDUINO_ENABLED=true in .env)")
        return None

    try:
        print(f"[Arduino] Starting Arduino agent on {arduino_port}...")

        arduino_agent = ArduinoDataAgent(
            serial_port=arduino_port,
            baud_rate=arduino_baud,
            model_name='gemini-2.5-flash',
            update_interval=1.0  # Read every 1 second
        )

        # Register callback
        arduino_agent.register_callback(on_arduino_data_update)

        # Start agent
        arduino_agent.start()

        print("[Arduino] Arduino agent started successfully")
        return arduino_agent

    except Exception as e:
        print(f"[Arduino] Failed to start: {e}")
        print("[Arduino] Continuing without Arduino (using mock data)")
        return None


if __name__ == '__main__':
    print("=" * 60)
    print("Helios AI Dashboard Starting...")
    print("=" * 60)
    print(f"Mock Data Mode: {dashboard_state['mock_mode']}")
    print(f"Dashboard URL: http://localhost:{Config.DASHBOARD_PORT}")
    print(f"Gemini Voice Chat: {'Enabled' if GEMINI_API_KEY else 'Disabled (GEMINI_API_KEY not set)'}")
    print("=" * 60)

    # Start Arduino agent (if enabled)
    start_arduino_agent()

    # Start background broadcast thread
    start_broadcast_thread()

    # Run Flask app with SocketIO
    socketio.run(
        app,
        host='0.0.0.0',
        port=Config.DASHBOARD_PORT,
        debug=Config.DEBUG_MODE,
        use_reloader=False  # Disable reloader to prevent double thread start
    )
