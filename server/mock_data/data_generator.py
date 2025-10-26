"""
Mock data generator for testing Helios AI without hardware
Generates realistic sensor data, status updates, and performance metrics
"""
import time
import random
import math
from typing import Dict


class MockDataGenerator:
    """Generates realistic mock data for all MQTT topics"""

    def __init__(self):
        self.start_time = time.time()
        self.pan_angle = 90.0  # Start facing east
        self.tilt_angle = 45.0
        self.mode = "Predictive"
        self.accumulated_energy_mwh = 0
        self.accumulated_energy_kwh = 0

    def get_sensor_data(self) -> Dict:
        """Generate mock sensor data (helios/sensors/raw)"""
        # Simulate solar panel output based on time of day
        current_time = time.time()
        elapsed = current_time - self.start_time

        # Simulate sun position changing (simple sine wave)
        sun_intensity = max(0, math.sin(elapsed / 20) * 0.8 + 0.2)  # 0-1 range

        # LDR values (higher = more light)
        base_ldr = 500 + int(sun_intensity * 300)
        ldr_tl = base_ldr + random.randint(-50, 50)
        ldr_tr = base_ldr + random.randint(-50, 50)
        ldr_bl = base_ldr + random.randint(-80, 30)
        ldr_br = base_ldr + random.randint(-80, 30)

        # Power generation (affected by sun intensity)
        panel_voltage = 4.5 + sun_intensity * 0.5 + random.uniform(-0.1, 0.1)
        panel_current = 100 + sun_intensity * 150 + random.uniform(-10, 10)
        panel_power = panel_voltage * panel_current

        return {
            "timestamp": int(current_time),
            "ldr_tl": ldr_tl,
            "ldr_tr": ldr_tr,
            "ldr_bl": ldr_bl,
            "ldr_br": ldr_br,
            "panel_voltage_V": round(panel_voltage, 2),
            "panel_current_mA": round(panel_current, 2),
            "panel_power_mW": round(panel_power, 2)
        }

    def get_status(self) -> Dict:
        """Generate mock status data (helios/status)"""
        current_time = time.time()
        elapsed = current_time - self.start_time

        # Simulate sun position changing
        sun_azimuth = 90 + (elapsed * 2) % 180  # Moves east to west
        sun_elevation = 30 + 20 * math.sin(elapsed / 15)

        # Panel follows sun with slight lag
        self.pan_angle = sun_azimuth + random.uniform(-2, 2)
        self.tilt_angle = sun_elevation + random.uniform(-1, 1)

        # Cloud cover changes slowly
        cloud_cover = 15 + 20 * math.sin(elapsed / 40)

        return {
            "timestamp": int(current_time),
            "mode": self.mode,
            "pan_angle_deg": round(self.pan_angle, 1),
            "tilt_angle_deg": round(self.tilt_angle, 1),
            "sun_azimuth_deg": round(sun_azimuth, 1),
            "sun_elevation_deg": round(sun_elevation, 1),
            "cloud_cover_pct": int(max(0, min(100, cloud_cover)))
        }

    def get_performance_delta(self) -> Dict:
        """Generate mock A/B comparison data (helios/ai/performance_delta)"""
        current_time = time.time()

        # Actual strategy (predictive) is usually better
        actual_power = 700 + random.uniform(-50, 100)
        shadow_power = actual_power * (0.85 + random.uniform(-0.05, 0.05))
        delta_pct = ((actual_power - shadow_power) / shadow_power) * 100

        return {
            "timestamp": int(current_time),
            "window_s": 600,
            "actual_strategy_power_mW": round(actual_power, 2),
            "shadow_strategy_power_mW": round(shadow_power, 2),
            "delta_pct": round(delta_pct, 2)
        }

    def get_impact_data(self) -> Dict:
        """Generate mock impact metrics (helios/impact)"""
        current_time = time.time()
        elapsed = current_time - self.start_time

        # Accumulate energy over time (mWh)
        energy_increment = (700 * (1/3600))  # 700mW for 1 second -> mWh
        self.accumulated_energy_mwh += energy_increment
        self.accumulated_energy_kwh = self.accumulated_energy_mwh / 1_000_000

        # Calculate savings
        usd_saved = self.accumulated_energy_kwh * 0.15  # $0.15 per kWh
        co2_g = self.accumulated_energy_kwh * 500  # 500g CO2 per kWh

        return {
            "timestamp": int(current_time),
            "energy_kWh": round(self.accumulated_energy_kwh, 6),
            "usd_saved": round(usd_saved, 4),
            "co2_g": round(co2_g, 2)
        }

    def get_safety_data(self) -> Dict:
        """Generate mock safety data (helios/safety)"""
        current_time = time.time()

        # Mostly normal, occasionally a warning
        servo_status = "normal" if random.random() > 0.05 else "warning"
        angle_violation = random.random() < 0.02
        temperature = 25 + random.uniform(-5, 15)

        return {
            "timestamp": int(current_time),
            "servo_status": servo_status,
            "angle_violation": angle_violation,
            "temperature_C": round(temperature, 1)
        }

    def get_voice_log_entry(self, command: str, response: str) -> Dict:
        """Generate mock voice log entry (helios/voice/log)"""
        return {
            "timestamp": int(time.time()),
            "command": command,
            "response": response
        }


if __name__ == "__main__":
    # Test mock data generator
    generator = MockDataGenerator()

    print("Mock Data Generator Test")
    print("=" * 50)

    print("\n[Sensor Data]")
    print(generator.get_sensor_data())

    print("\n[Status]")
    print(generator.get_status())

    print("\n[Performance Delta]")
    print(generator.get_performance_delta())

    print("\n[Impact]")
    print(generator.get_impact_data())

    print("\n[Safety]")
    print(generator.get_safety_data())

    # Simulate data over 3 seconds
    print("\n" + "=" * 50)
    print("Simulating data over 3 seconds...")
    for i in range(3):
        time.sleep(1)
        sensor_data = generator.get_sensor_data()
        print(f"T+{i+1}s: Power = {sensor_data['panel_power_mW']:.2f} mW")
