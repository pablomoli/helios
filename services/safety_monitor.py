"""
Safety Monitor Service
Monitors system data and emits safety alerts
Implements safety limits for servos, temperature, and power
"""
import time
import sys
from pathlib import Path
import socketio

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config import Config, Events

# Safety limits
SAFETY_LIMITS = {
    'pan_angle_min': 0,
    'pan_angle_max': 180,
    'tilt_angle_min': 0,
    'tilt_angle_max': 180,
    'max_temperature_c': 80,  # Maximum safe temperature
    'max_voltage_v': 6.0,  # Maximum safe voltage
    'max_current_ma': 500,  # Maximum safe current
    'max_power_mw': 3000,  # Maximum safe power
    'max_movement_rate_deg_per_sec': 30,  # Maximum servo speed
}


class SafetyMonitor:
    """Monitors system for safety violations"""

    def __init__(self, websocket_url):
        self.websocket_url = websocket_url
        self.sio = socketio.Client()
        self.latest_data = {
            'sensors': {},
            'status': {},
        }
        self.last_angles = {'pan': 90, 'tilt': 90}
        self.last_check_time = time.time()

        # Set up event handlers
        self.setup_handlers()

    def setup_handlers(self):
        """Set up WebSocket event handlers"""

        @self.sio.on('connect')
        def on_connect():
            print(f"[Safety Monitor] Connected to {self.websocket_url}")

        @self.sio.on(Events.SENSORS_RAW)
        def on_sensors(data):
            self.latest_data['sensors'] = data
            self.check_sensor_safety(data)

        @self.sio.on(Events.STATUS)
        def on_status(data):
            self.latest_data['status'] = data
            self.check_servo_safety(data)

        @self.sio.on('disconnect')
        def on_disconnect():
            print("[Safety Monitor] Disconnected from WebSocket server")

    def connect(self):
        """Connect to WebSocket server"""
        try:
            self.sio.connect(self.websocket_url)
            print("[Safety Monitor] Connected successfully")
            return True
        except Exception as e:
            print(f"[Safety Monitor] Connection failed: {e}")
            return False

    def check_sensor_safety(self, data):
        """Check sensor data for safety violations"""
        alerts = []

        # Check voltage
        voltage = data.get('panel_voltage_V', 0)
        if voltage > SAFETY_LIMITS['max_voltage_v']:
            alerts.append(f"Voltage too high: {voltage}V (max {SAFETY_LIMITS['max_voltage_v']}V)")

        # Check current
        current = data.get('panel_current_mA', 0)
        if current > SAFETY_LIMITS['max_current_ma']:
            alerts.append(f"Current too high: {current}mA (max {SAFETY_LIMITS['max_current_ma']}mA)")

        # Check power
        power = data.get('panel_power_mW', 0)
        if power > SAFETY_LIMITS['max_power_mw']:
            alerts.append(f"Power too high: {power}mW (max {SAFETY_LIMITS['max_power_mw']}mW)")

        if alerts:
            self.emit_safety_alert(alerts, 'sensor_limits')

    def check_servo_safety(self, data):
        """Check servo positions and movement for safety violations"""
        alerts = []

        # Check pan angle limits
        pan = data.get('pan_angle_deg', 90)
        if pan < SAFETY_LIMITS['pan_angle_min'] or pan > SAFETY_LIMITS['pan_angle_max']:
            alerts.append(f"Pan angle out of range: {pan}° (range {SAFETY_LIMITS['pan_angle_min']}-{SAFETY_LIMITS['pan_angle_max']}°)")

        # Check tilt angle limits
        tilt = data.get('tilt_angle_deg', 90)
        if tilt < SAFETY_LIMITS['tilt_angle_min'] or tilt > SAFETY_LIMITS['tilt_angle_max']:
            alerts.append(f"Tilt angle out of range: {tilt}° (range {SAFETY_LIMITS['tilt_angle_min']}-{SAFETY_LIMITS['tilt_angle_max']}°)")

        # Check movement rate
        current_time = time.time()
        time_delta = current_time - self.last_check_time

        if time_delta > 0:
            pan_delta = abs(pan - self.last_angles['pan'])
            tilt_delta = abs(tilt - self.last_angles['tilt'])

            pan_rate = pan_delta / time_delta
            tilt_rate = tilt_delta / time_delta

            if pan_rate > SAFETY_LIMITS['max_movement_rate_deg_per_sec']:
                alerts.append(f"Pan moving too fast: {pan_rate:.1f}°/s (max {SAFETY_LIMITS['max_movement_rate_deg_per_sec']}°/s)")

            if tilt_rate > SAFETY_LIMITS['max_movement_rate_deg_per_sec']:
                alerts.append(f"Tilt moving too fast: {tilt_rate:.1f}°/s (max {SAFETY_LIMITS['max_movement_rate_deg_per_sec']}°/s)")

        # Update tracking
        self.last_angles = {'pan': pan, 'tilt': tilt}
        self.last_check_time = current_time

        if alerts:
            self.emit_safety_alert(alerts, 'servo_limits')
        else:
            # Emit normal status
            self.emit_safety_status('normal', pan, tilt)

    def emit_safety_alert(self, alerts, alert_type):
        """Emit safety alert to WebSocket"""
        safety_data = {
            'timestamp': int(time.time()),
            'alert': True,
            'alert_type': alert_type,
            'messages': alerts,
            'servo_status': 'warning',
            'angle_violation': True
        }

        print(f"[Safety Monitor] ⚠️ ALERT: {', '.join(alerts)}")
        self.sio.emit(Events.SAFETY, safety_data)

    def emit_safety_status(self, status, pan, tilt):
        """Emit normal safety status"""
        safety_data = {
            'timestamp': int(time.time()),
            'alert': False,
            'servo_status': status,
            'angle_violation': False,
            'pan_angle_deg': pan,
            'tilt_angle_deg': tilt,
            'temperature_C': self.latest_data['sensors'].get('temperature_C', 25)
        }

        self.sio.emit(Events.SAFETY, safety_data)

    def run(self):
        """Run the safety monitor"""
        print("[Safety Monitor] Starting...")
        print(f"[Safety Monitor] Safety limits:")
        for key, value in SAFETY_LIMITS.items():
            print(f"  {key}: {value}")

        # Connect to WebSocket server
        while not self.connect():
            print("[Safety Monitor] Retrying connection in 5 seconds...")
            time.sleep(5)

        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Safety Monitor] Shutting down...")
            self.sio.disconnect()


def main():
    """Main entry point"""
    monitor = SafetyMonitor(Config.WEBSOCKET_SERVER_URL)
    monitor.run()


if __name__ == "__main__":
    main()
