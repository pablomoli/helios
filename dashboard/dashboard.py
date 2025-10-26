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
from config import Config, Events
from mock_data.data_generator import MockDataGenerator
from dashboard.voice_handler import process_voice_query, update_system_data, simple_wake_word_detection

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


@app.route('/api/gemini-config')
def get_gemini_config():
    """Provide Gemini API configuration"""
    return {
        "api_key": Config.GOOGLE_GENAI_API_KEY
    }


@app.route('/api/voice-query', methods=['POST'])
def handle_voice_query_api():
    """Handle voice query from browser"""
    from flask import request, jsonify

    data = request.json
    audio_data = data.get('audio')
    system_data = data.get('system_data', {})

    if not audio_data:
        return jsonify({'error': 'No audio data'}), 400

    try:
        # Update system data for context
        if system_data.get('sensors'):
            update_system_data('sensors', system_data['sensors'])
        if system_data.get('status'):
            update_system_data('status', system_data['status'])
        if system_data.get('impact'):
            update_system_data('impact', system_data['impact'])
        if system_data.get('safety'):
            update_system_data('safety', system_data['safety'])

        # Detect wake word
        wake_word_detected = simple_wake_word_detection(audio_data)

        if wake_word_detected:
            # Process query
            result = process_voice_query(audio_data, wake_word_detected=True)

            return jsonify({
                'wake_word_detected': True,
                'response_text': result.get('response_text', ''),
                'success': result.get('success', False)
            })
        else:
            return jsonify({
                'wake_word_detected': False
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


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

    if topic == 'all' or topic == Events.SENSORS_RAW:
        emit('sensor_data', mock_generator.get_sensor_data())

    if topic == 'all' or topic == Events.STATUS:
        emit('status_data', mock_generator.get_status())

    if topic == 'all' or topic == Events.AI_PERFORMANCE_DELTA:
        emit('performance_delta', mock_generator.get_performance_delta())

    if topic == 'all' or topic == Events.IMPACT:
        emit('impact_data', mock_generator.get_impact_data())

    if topic == 'all' or topic == Events.SAFETY:
        emit('safety_data', mock_generator.get_safety_data())


@socketio.on('voice_input')
def handle_voice_input(data):
    """
    Handle voice input from browser
    Expects: { "audio": base64_audio_data }
    """
    try:
        audio_data = data.get('audio')
        if not audio_data:
            emit('voice_response', {'error': 'No audio data provided'})
            return

        print(f"[Voice] Received audio input, checking for wake word...")

        # Detect wake word
        wake_word_detected = simple_wake_word_detection(audio_data)

        if wake_word_detected:
            print(f"[Voice] Wake word 'Helios' detected!")
            # Emit wake word detection event
            socketio.emit('wake_word_detected', {'timestamp': time.time()})

            # Process the query
            result = process_voice_query(audio_data, wake_word_detected=True)

            if result.get('success'):
                response_text = result.get('response_text', '')
                print(f"[Voice] Response: {response_text}")

                # Emit response
                emit('voice_response', {
                    'text': response_text,
                    'timestamp': time.time()
                })

                # Log to voice log
                socketio.emit(Events.VOICE_LOG, {
                    'type': 'response',
                    'text': response_text
                })
            else:
                emit('voice_response', {
                    'error': result.get('message', 'Error processing query')
                })
        else:
            print(f"[Voice] No wake word detected, ignoring")
            # Don't respond if no wake word
            pass

    except Exception as e:
        print(f"[Voice] Error: {e}")
        emit('voice_response', {'error': str(e)})


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
        use_reloader=False,  # Disable reloader to prevent double thread start
        allow_unsafe_werkzeug=True
    )
