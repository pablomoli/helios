"""
Flask Dashboard with WebSocket support for Helios AI
Serves the web interface and streams real-time data
"""
from flask import Flask, render_template, request, jsonify, abort
from flask_socketio import SocketIO, emit
import time
import sys
from pathlib import Path
import os
from threading import Thread, Lock
import requests
from cachetools import TTLCache, LRUCache

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config, Topics
from mock_data.data_generator import MockDataGenerator

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

# Mock data generator
mock_generator = MockDataGenerator()

# Global state
dashboard_state = {
    "mock_mode": Config.MOCK_DATA_MODE,
    "connected_clients": 0
}

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


if __name__ == '__main__':
    print("=" * 60)
    print("Helios AI Dashboard Starting...")
    print("=" * 60)
    print(f"Mock Data Mode: {dashboard_state['mock_mode']}")
    print(f"Dashboard URL: http://localhost:{Config.DASHBOARD_PORT}")
    print("=" * 60)

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
