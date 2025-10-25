"""
Flask Dashboard with WebSocket support for Helios AI
Serves the web interface and streams real-time data
"""
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time
import sys
from pathlib import Path
from threading import Thread

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config, Topics
from mock_data.data_generator import MockDataGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'helios_ai_secret_key_change_in_production'
socketio = SocketIO(app, cors_allowed_origins="*")

# Mock data generator
mock_generator = MockDataGenerator()

# Global state
dashboard_state = {
    "mock_mode": Config.MOCK_DATA_MODE,
    "connected_clients": 0
}


@app.route('/')
def index():
    """Serve the main dashboard page"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mock_mode": dashboard_state["mock_mode"],
        "connected_clients": dashboard_state["connected_clients"],
        "timestamp": int(time.time())
    }


@app.route('/api/config')
def get_config():
    """Provide safe configuration to frontend"""
    return {
        "openweather_api_key": Config.OPENWEATHER_API_KEY,
        "default_lat": Config.WEATHER_LAT,
        "default_lon": Config.WEATHER_LON
    }


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    dashboard_state["connected_clients"] += 1
    print(f"[Dashboard] Client connected (total: {dashboard_state['connected_clients']})")

    # Send initial connection confirmation
    emit('connection_status', {
        "status": "connected",
        "mock_mode": dashboard_state["mock_mode"],
        "timestamp": int(time.time())
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    dashboard_state["connected_clients"] -= 1
    print(f"[Dashboard] Client disconnected (total: {dashboard_state['connected_clients']})")


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

        if dashboard_state["connected_clients"] > 0:
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
