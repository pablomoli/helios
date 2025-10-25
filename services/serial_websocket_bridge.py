"""
Serial to WebSocket Bridge with Flask-SocketIO
Reads data from Arduino via USB serial and broadcasts to WebSocket clients
Listens for WebSocket commands and sends them to Arduino
"""
import serial
import json
import time
import sys
import threading
from pathlib import Path
from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config import Config, Events

# Serial configuration
SERIAL_PORT = '/dev/ttyUSB0'  # Change to match your Arduino port
SERIAL_BAUD_RATE = 9600
RECONNECT_DELAY = 5  # seconds

# Flask app
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global serial connection
serial_conn = None
serial_connected = False


def connect_serial():
    """Establish serial connection to Arduino"""
    global serial_conn, serial_connected

    try:
        print(f"[Serial Bridge] Connecting to Arduino on {SERIAL_PORT} at {SERIAL_BAUD_RATE} baud...")
        serial_conn = serial.Serial(
            port=SERIAL_PORT,
            baudrate=SERIAL_BAUD_RATE,
            timeout=1
        )
        # Wait for Arduino to reset after serial connection
        time.sleep(2)
        serial_connected = True
        print(f"[Serial Bridge] Connected successfully!")
        socketio.emit('connection_status', {'arduino_connected': True})
        return True
    except serial.SerialException as e:
        print(f"[Serial Bridge] Connection failed: {e}")
        serial_connected = False
        socketio.emit('connection_status', {'arduino_connected': False, 'error': str(e)})
        return False


def disconnect_serial():
    """Close serial connection"""
    global serial_conn, serial_connected

    if serial_conn and serial_conn.is_open:
        serial_conn.close()
        serial_connected = False
        print("[Serial Bridge] Disconnected")
        socketio.emit('connection_status', {'arduino_connected': False})


def read_serial_loop():
    """Background thread to continuously read from Arduino"""
    global serial_conn, serial_connected

    while True:
        if not serial_connected:
            # Attempt to reconnect
            if not connect_serial():
                time.sleep(RECONNECT_DELAY)
                continue

        try:
            if serial_conn and serial_conn.in_waiting > 0:
                line = serial_conn.readline().decode('utf-8').strip()

                if line:
                    # Parse Arduino message
                    try:
                        data = json.loads(line)
                        msg_type = data.get('type', 'unknown')

                        # Remove 'type' field before emitting
                        if 'type' in data:
                            del data['type']

                        # Emit to appropriate WebSocket event
                        if msg_type == 'sensors':
                            socketio.emit(Events.SENSORS_RAW, data)
                            print(f"[SENSORS] Power: {data.get('panel_power_mW', 0):.1f} mW")
                        elif msg_type == 'status':
                            socketio.emit(Events.STATUS, data)
                            print(f"[STATUS] Mode: {data.get('mode', 'Unknown')}, Pan: {data.get('pan_angle_deg', 0)}°")
                        elif msg_type == 'energy':
                            socketio.emit(Events.IMPACT, data)
                            print(f"[ENERGY] Saved: {data.get('energy_saved_kWh', 0)} kWh")
                        elif msg_type == 'safety':
                            socketio.emit(Events.SAFETY, data)
                            if data.get('alert', False):
                                print(f"[SAFETY] ⚠️ ALERT: {data.get('message', 'Unknown')}")
                        else:
                            print(f"[UNKNOWN] {msg_type}: {data}")

                    except json.JSONDecodeError:
                        print(f"[Serial Bridge] Invalid JSON: {line}")

        except (serial.SerialException, UnicodeDecodeError) as e:
            print(f"[Serial Bridge] Read error: {e}")
            serial_connected = False
            disconnect_serial()

        time.sleep(0.01)  # Small delay to prevent CPU spinning


def send_to_arduino(command):
    """Send command to Arduino"""
    global serial_conn, serial_connected

    if not serial_connected or not serial_conn:
        print("[Serial Bridge] Not connected, cannot send command")
        return False

    try:
        command_str = json.dumps(command) + '\n'
        serial_conn.write(command_str.encode('utf-8'))
        print(f"[Arduino CMD] {command}")
        return True
    except serial.SerialException as e:
        print(f"[Serial Bridge] Write error: {e}")
        serial_connected = False
        return False


# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Client connected to WebSocket"""
    print(f"[WebSocket] Client connected")
    emit('connection_status', {'arduino_connected': serial_connected})


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected from WebSocket"""
    print(f"[WebSocket] Client disconnected")


@socketio.on(Events.COMMAND_POSITION)
def handle_position_command(data):
    """Receive position command from client and send to Arduino"""
    print(f"[Position CMD] {data}")
    command = {
        'type': 'position',
        'pan_angle_deg': data.get('pan_angle_deg', 90),
        'tilt_angle_deg': data.get('tilt_angle_deg', 45)
    }
    send_to_arduino(command)


@socketio.on('command_mode')
def handle_mode_command(data):
    """Receive mode switch command from client and send to Arduino"""
    print(f"[Mode CMD] {data}")
    command = {
        'type': 'mode',
        'mode': data.get('mode', 'Reactive')
    }
    send_to_arduino(command)


@app.route('/')
def index():
    """Simple status page"""
    return f"""
    <html>
    <head><title>Helios Serial Bridge</title></head>
    <body>
        <h1>Helios Serial Bridge</h1>
        <p>WebSocket Server Running</p>
        <p>Arduino Connection: {'✅ Connected' if serial_connected else '❌ Disconnected'}</p>
        <p>Serial Port: {SERIAL_PORT}</p>
        <p>Baud Rate: {SERIAL_BAUD_RATE}</p>
    </body>
    </html>
    """


def main():
    """Start the WebSocket server and serial reader"""
    print("[Serial Bridge] Starting WebSocket server...")
    print(f"[Serial Bridge] Configured for port: {SERIAL_PORT}")
    print(f"[Serial Bridge] WebSocket server: http://0.0.0.0:{Config.DASHBOARD_PORT}")

    # Start serial reading thread
    serial_thread = threading.Thread(target=read_serial_loop, daemon=True)
    serial_thread.start()

    # Start WebSocket server
    socketio.run(app, host='0.0.0.0', port=Config.DASHBOARD_PORT, debug=False)


if __name__ == "__main__":
    main()
