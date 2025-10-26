"""
Arduino Data Collection Agent
Uses Gemini to parse and structure sensor data from Arduino via Serial
"""
import serial
import json
import time
import threading
from typing import Dict, Optional, Callable
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    load_dotenv()
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install google-generativeai python-dotenv pyserial")
    sys.exit(1)


class ArduinoDataAgent:
    """
    Agent that reads Arduino serial data and parses it using Gemini
    """

    def __init__(
        self,
        serial_port: str = '/dev/ttyUSB0',
        baud_rate: int = 9600,
        model_name: str = 'gemini-2.5-flash',
        update_interval: float = 1.0
    ):
        """
        Initialize Arduino Data Agent

        Args:
            serial_port: Arduino serial port (e.g., '/dev/ttyUSB0' on Linux, 'COM3' on Windows)
            baud_rate: Serial communication speed (must match Arduino)
            model_name: Gemini model for parsing (gemini-2.5-flash or gemini-1.5-flash)
            update_interval: How often to read from Arduino (seconds)
        """
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.update_interval = update_interval

        # Current parsed data
        self.current_data: Dict = {}
        self.last_raw_data: str = ""
        self.last_update_time: float = 0

        # Callbacks for data updates
        self.callbacks: list[Callable] = []

        # Threading
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # Serial connection
        self.serial: Optional[serial.Serial] = None

        # Gemini setup
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

        print(f"[ArduinoAgent] Initialized with model: {model_name}")
        print(f"[ArduinoAgent] Serial port: {serial_port} @ {baud_rate} baud")

    def connect_serial(self) -> bool:
        """Connect to Arduino via serial port"""
        try:
            self.serial = serial.Serial(
                self.serial_port,
                self.baud_rate,
                timeout=2
            )
            time.sleep(2)  # Wait for Arduino to reset
            print(f"[ArduinoAgent] Connected to {self.serial_port}")
            return True
        except serial.SerialException as e:
            print(f"[ArduinoAgent] Failed to connect: {e}")
            return False

    def parse_with_gemini(self, raw_data: str) -> Dict:
        """
        Use Gemini to parse Arduino sensor data

        Args:
            raw_data: Raw text from Arduino

        Returns:
            Parsed data as dictionary
        """
        prompt = f"""Parse this Arduino sensor data into valid JSON format.

Raw data from Arduino:
{raw_data}

Expected fields (if available in the data):
- voltage: Panel voltage in volts (V)
- current: Panel current in milliamps (mA)
- power: Power output in milliwatts (mW)
- temperature: System temperature in Celsius (°C)
- azimuth: Solar panel azimuth angle in degrees
- elevation: Solar panel elevation angle in degrees
- cloud_coverage: Cloud coverage percentage (0-100)
- timestamp: Current timestamp

CRITICAL:
- Return ONLY valid JSON, no markdown, no explanation
- Use null for missing fields
- Convert all numeric values to proper numbers (not strings)
- If the data is garbled or unclear, extract what you can and use null for the rest

Example output format:
{{"voltage": 12.5, "current": 850, "power": 10625, "temperature": 25.3, "azimuth": 180, "elevation": 45, "cloud_coverage": 20, "timestamp": "2024-10-26T12:00:00"}}

Now parse the data above:"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,  # Low temperature for consistent parsing
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 500,
                }
            )

            # Extract JSON from response
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]

            parsed = json.loads(response_text.strip())
            return parsed

        except json.JSONDecodeError as e:
            print(f"[ArduinoAgent] JSON parse error: {e}")
            print(f"[ArduinoAgent] Response was: {response.text}")
            return {"error": "parse_failed", "raw": raw_data}
        except Exception as e:
            print(f"[ArduinoAgent] Gemini error: {e}")
            return {"error": str(e), "raw": raw_data}

    def read_arduino(self) -> Optional[str]:
        """Read one line from Arduino"""
        try:
            if self.serial and self.serial.in_waiting > 0:
                raw_data = self.serial.readline().decode('utf-8', errors='ignore').strip()
                return raw_data
            return None
        except serial.SerialException as e:
            print(f"[ArduinoAgent] Read error: {e}")
            return None

    def update_loop(self):
        """Main loop: read Arduino data and parse with Gemini"""
        print("[ArduinoAgent] Update loop started")

        while self.running:
            try:
                # Read from Arduino
                raw_data = self.read_arduino()

                if raw_data:
                    self.last_raw_data = raw_data
                    print(f"[ArduinoAgent] Raw: {raw_data}")

                    # Parse with Gemini
                    parsed_data = self.parse_with_gemini(raw_data)

                    # Update current data
                    self.current_data = parsed_data
                    self.last_update_time = time.time()

                    print(f"[ArduinoAgent] Parsed: {json.dumps(parsed_data, indent=2)}")

                    # Notify callbacks
                    for callback in self.callbacks:
                        try:
                            callback(parsed_data)
                        except Exception as e:
                            print(f"[ArduinoAgent] Callback error: {e}")

                # Wait before next read
                time.sleep(self.update_interval)

            except Exception as e:
                print(f"[ArduinoAgent] Loop error: {e}")
                time.sleep(self.update_interval)

        print("[ArduinoAgent] Update loop stopped")

    def register_callback(self, callback: Callable):
        """Register a callback to be called when new data arrives"""
        self.callbacks.append(callback)

    def start(self):
        """Start the Arduino data collection agent"""
        if self.running:
            print("[ArduinoAgent] Already running")
            return

        # Connect to serial
        if not self.connect_serial():
            raise RuntimeError("Failed to connect to Arduino")

        # Start update thread
        self.running = True
        self.thread = threading.Thread(target=self.update_loop, daemon=True)
        self.thread.start()

        print("[ArduinoAgent] Started")

    def stop(self):
        """Stop the agent"""
        print("[ArduinoAgent] Stopping...")
        self.running = False

        if self.thread:
            self.thread.join(timeout=5)

        if self.serial:
            self.serial.close()

        print("[ArduinoAgent] Stopped")

    def get_current_data(self) -> Dict:
        """Get the most recent parsed data"""
        return self.current_data.copy()

    def get_data_age(self) -> float:
        """Get age of current data in seconds"""
        if self.last_update_time == 0:
            return float('inf')
        return time.time() - self.last_update_time


# Test function
def test_arduino_agent():
    """Test the Arduino agent"""
    print("=" * 60)
    print("Arduino Data Agent Test")
    print("=" * 60)

    # Detect serial port
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())

    if not ports:
        print("No serial ports found!")
        print("Make sure Arduino is connected via USB")
        return

    print("\nAvailable serial ports:")
    for i, port in enumerate(ports):
        print(f"  {i+1}. {port.device} - {port.description}")

    # Use first port by default
    port_choice = input(f"\nSelect port (1-{len(ports)}) [1]: ").strip() or "1"
    selected_port = ports[int(port_choice) - 1].device

    print(f"\nUsing: {selected_port}")
    print("\nStarting agent...")

    # Create agent
    agent = ArduinoDataAgent(
        serial_port=selected_port,
        baud_rate=9600,
        update_interval=1.0
    )

    # Register callback to print data
    def print_data(data):
        print(f"[Callback] New data: {json.dumps(data, indent=2)}")

    agent.register_callback(print_data)

    # Start
    try:
        agent.start()

        print("\nAgent running. Press Ctrl+C to stop...")
        print("=" * 60)

        # Keep running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nStopping agent...")
        agent.stop()
        print("Test complete!")


if __name__ == "__main__":
    test_arduino_agent()
