"""
MQTT client wrapper with automatic reconnection and error handling
"""
import paho.mqtt.client as mqtt
import time
import json
from typing import Callable, Dict, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config, Topics


class HeliosMQTTClient:
    """MQTT client with reconnection logic for Helios AI"""

    def __init__(self, client_id: str = "helios_client"):
        self.client_id = client_id
        self.broker_host = Config.MQTT_BROKER_HOST
        self.broker_port = Config.MQTT_BROKER_PORT
        self.keep_alive = Config.MQTT_KEEP_ALIVE

        # Create MQTT client
        self.client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)

        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # Subscription callbacks
        self._topic_callbacks: Dict[str, Callable] = {}

        # Connection state
        self.connected = False
        self.connection_attempts = 0

    def connect(self) -> bool:
        """Connect to MQTT broker with retry logic"""
        try:
            print(f"[MQTT] Connecting to {self.broker_host}:{self.broker_port}...")
            self.client.connect(self.broker_host, self.broker_port, self.keep_alive)
            self.client.loop_start()
            return True
        except Exception as e:
            print(f"[MQTT] Connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False
        print("[MQTT] Disconnected")

    def subscribe(self, topic: str, callback: Optional[Callable] = None, qos: int = 1):
        """
        Subscribe to a topic with optional callback
        Args:
            topic: MQTT topic to subscribe to
            callback: Function to call when message received (takes topic, payload as args)
            qos: Quality of Service level (0, 1, or 2)
        """
        self.client.subscribe(topic, qos=qos)
        if callback:
            self._topic_callbacks[topic] = callback
        print(f"[MQTT] Subscribed to {topic}")

    def publish(self, topic: str, payload: Dict, qos: int = 1) -> bool:
        """
        Publish a message to a topic
        Args:
            topic: MQTT topic to publish to
            payload: Dictionary to publish (will be JSON encoded)
            qos: Quality of Service level
        Returns:
            True if published successfully
        """
        try:
            payload_json = json.dumps(payload)
            result = self.client.publish(topic, payload_json, qos=qos)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            print(f"[MQTT] Publish failed: {e}")
            return False

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            self.connected = True
            self.connection_attempts = 0
            print(f"[MQTT] Connected successfully (client: {self.client_id})")
        else:
            self.connected = False
            print(f"[MQTT] Connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        self.connected = False
        if rc != 0:
            print(f"[MQTT] Unexpected disconnect (rc: {rc}), reconnecting...")
            self._reconnect()

    def _on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            payload = json.loads(msg.payload.decode())

            # Call topic-specific callback if registered
            if msg.topic in self._topic_callbacks:
                self._topic_callbacks[msg.topic](msg.topic, payload)

        except json.JSONDecodeError:
            print(f"[MQTT] Invalid JSON on {msg.topic}: {msg.payload}")
        except Exception as e:
            print(f"[MQTT] Error processing message on {msg.topic}: {e}")

    def _reconnect(self):
        """Attempt to reconnect with exponential backoff"""
        self.connection_attempts += 1
        delay = min(2 ** self.connection_attempts, 60)  # Max 60 seconds
        print(f"[MQTT] Reconnecting in {delay}s...")
        time.sleep(delay)
        self.connect()


if __name__ == "__main__":
    # Test MQTT client
    def test_callback(topic, payload):
        print(f"[TEST] Received on {topic}: {payload}")

    client = HeliosMQTTClient("test_client")

    # Try to connect (will fail if broker not running)
    if client.connect():
        print("[TEST] Connected to broker")

        # Subscribe to test topics
        client.subscribe(Topics.SENSORS_RAW, test_callback)
        client.subscribe(Topics.STATUS, test_callback)

        # Publish test message
        test_data = {
            "timestamp": int(time.time()),
            "test": True,
            "message": "Hello from Helios"
        }
        client.publish("helios/test", test_data)

        print("[TEST] Running for 5 seconds...")
        time.sleep(5)

        client.disconnect()
    else:
        print("[TEST] Could not connect to broker")
        print(f"[TEST] Make sure Mosquitto is running on {Config.MQTT_BROKER_HOST}:{Config.MQTT_BROKER_PORT}")
