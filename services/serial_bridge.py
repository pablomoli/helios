"""
Serial Bridge - Arduino to WebSocket
Reads data from Arduino via USB serial and broadcasts to WebSocket clients
"""
import serial
import json
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config import Config, Events

# Serial configuration
SERIAL_PORT = '/dev/ttyUSB0'  # Change to match your Arduino port (Windows: COM3, Mac: /dev/tty.usbserial-*)
SERIAL_BAUD_RATE = 9600
RECONNECT_DELAY = 5  # seconds


class SerialBridge:
    """Bridges Arduino serial data to WebSocket events"""

    def __init__(self, port=SERIAL_PORT, baud_rate=SERIAL_BAUD_RATE):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.connected = False

    def connect(self):
        """Establish serial connection to Arduino"""
        try:
            print(f"[Serial Bridge] Connecting to Arduino on {self.port} at {self.baud_rate} baud...")
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=1
            )
            # Wait for Arduino to reset after serial connection
            time.sleep(2)
            self.connected = True
            print(f"[Serial Bridge] Connected successfully!")
            return True
        except serial.SerialException as e:
            print(f"[Serial Bridge] Connection failed: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Close serial connection"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.connected = False
            print("[Serial Bridge] Disconnected")

    def read_line(self):
        """Read a line from Arduino serial"""
        if not self.connected or not self.serial_conn:
            return None

        try:
            if self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode('utf-8').strip()
                return line
        except (serial.SerialException, UnicodeDecodeError) as e:
            print(f"[Serial Bridge] Read error: {e}")
            self.connected = False

        return None

    def write_command(self, command):
        """Send command to Arduino"""
        if not self.connected or not self.serial_conn:
            print("[Serial Bridge] Not connected, cannot send command")
            return False

        try:
            command_str = json.dumps(command) + '\n'
            self.serial_conn.write(command_str.encode('utf-8'))
            return True
        except serial.SerialException as e:
            print(f"[Serial Bridge] Write error: {e}")
            self.connected = False
            return False

    def parse_arduino_message(self, line):
        """
        Parse Arduino JSON message and determine event type

        Expected Arduino message format:
        {
            "type": "sensors",  // or "status", "energy", "safety"
            "timestamp": 1234567890,
            "ldr_tl": 800,
            "ldr_tr": 750,
            "ldr_bl": 600,
            "ldr_br": 580,
            "panel_voltage_V": 5.0,
            "panel_current_mA": 150.0,
            "panel_power_mW": 750.0,
            "energy_saved_kWh": 0.0012
        }
        """
        try:
            data = json.loads(line)
            msg_type = data.get('type', 'unknown')

            # Remove 'type' field before returning data
            if 'type' in data:
                del data['type']

            return msg_type, data
        except json.JSONDecodeError:
            print(f"[Serial Bridge] Invalid JSON: {line}")
            return None, None


def main():
    """Main loop - reads from Arduino and prints to console"""
    bridge = SerialBridge()

    print("[Serial Bridge] Starting...")
    print(f"[Serial Bridge] Configured for port: {SERIAL_PORT}")
    print("[Serial Bridge] Press Ctrl+C to exit")

    try:
        # Connect to Arduino
        while not bridge.connect():
            print(f"[Serial Bridge] Retrying in {RECONNECT_DELAY} seconds...")
            time.sleep(RECONNECT_DELAY)

        # Main read loop
        while True:
            line = bridge.read_line()

            if line:
                msg_type, data = bridge.parse_arduino_message(line)

                if msg_type and data:
                    print(f"[{msg_type.upper()}] {json.dumps(data, indent=2)}")

            # Reconnect if connection lost
            if not bridge.connected:
                print("[Serial Bridge] Connection lost, attempting to reconnect...")
                while not bridge.connect():
                    time.sleep(RECONNECT_DELAY)

            time.sleep(0.01)  # Small delay to prevent CPU spinning

    except KeyboardInterrupt:
        print("\n[Serial Bridge] Shutting down...")
    finally:
        bridge.disconnect()


if __name__ == "__main__":
    main()
