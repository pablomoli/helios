"""
Centralized configuration loader for Helios AI
Loads environment variables from .env file and provides validated config values
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Main configuration class"""

    # WebSocket Settings
    WEBSOCKET_SERVER_URL = os.getenv('WEBSOCKET_SERVER_URL', 'ws://localhost:5000')

    # OpenWeatherMap API (NEVER log or print this!)
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

    # Location Settings
    WEATHER_LAT = float(os.getenv('WEATHER_LAT', 37.7749))
    WEATHER_LON = float(os.getenv('WEATHER_LON', -122.4194))
    WEATHER_CACHE_TTL = int(os.getenv('WEATHER_CACHE_TTL', 900))

    # Dashboard Settings
    DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', 5000))
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'

    # System Settings
    MOCK_DATA_MODE = os.getenv('MOCK_DATA_MODE', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Porcupine Wake Word
    PORCUPINE_ACCESS_KEY = os.getenv('PORCUPINE_ACCESS_KEY')

    # ADK Settings
    ADK_PROJECT_ID = os.getenv('ADK_PROJECT_ID')

    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        errors = []

        if not cls.OPENWEATHER_API_KEY:
            errors.append("OPENWEATHER_API_KEY is not set in .env file")

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

        return True

    @classmethod
    def get_safe_config_string(cls):
        """Returns a safe string representation without secrets"""
        return f"""
Helios AI Configuration:
  WebSocket Server: {cls.WEBSOCKET_SERVER_URL}
  Location: ({cls.WEATHER_LAT}, {cls.WEATHER_LON})
  Dashboard Port: {cls.DASHBOARD_PORT}
  Mock Data Mode: {cls.MOCK_DATA_MODE}
  Debug Mode: {cls.DEBUG_MODE}
  OpenWeather API: {'Configured [OK]' if cls.OPENWEATHER_API_KEY else 'Missing [X]'}
  Porcupine Key: {'Configured [OK]' if cls.PORCUPINE_ACCESS_KEY else 'Missing [X]'}
        """.strip()


# WebSocket Events (centralized for consistency)
class Events:
    """WebSocket event definitions"""
    SENSORS_RAW = "sensors_raw"
    STATUS = "status"
    COMMAND_POSITION = "command_position"
    AI_PERFORMANCE_DELTA = "ai_performance_delta"
    IMPACT = "impact"
    SAFETY = "safety"
    VOICE_LOG = "voice_log"


if __name__ == "__main__":
    # Test configuration loading
    try:
        Config.validate()
        print("[OK] Configuration loaded successfully!")
        print(Config.get_safe_config_string())
    except ValueError as e:
        print(f"[ERROR] Configuration error: {e}")
