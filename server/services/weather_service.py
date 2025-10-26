"""
Weather service for fetching cloud cover data from OpenWeatherMap API
Includes caching and fallback mechanisms for stability
"""
import requests
import time
import sys
from pathlib import Path
from typing import Optional, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config


class WeatherService:
    """Fetches and caches weather data from OpenWeatherMap"""

    def __init__(self):
        self.api_key = Config.OPENWEATHER_API_KEY
        self.lat = Config.WEATHER_LAT
        self.lon = Config.WEATHER_LON
        self.cache_ttl = Config.WEATHER_CACHE_TTL

        # Cache storage
        self._cached_data: Optional[Dict] = None
        self._cache_timestamp: float = 0

        # API endpoint
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def get_cloud_cover(self) -> Dict[str, any]:
        """
        Get current cloud cover percentage
        Returns dict with cloud_cover_pct and timestamp
        """
        # Check cache first
        if self._is_cache_valid():
            return self._cached_data

        # Fetch fresh data
        try:
            data = self._fetch_from_api()
            self._update_cache(data)
            return data
        except Exception as e:
            # Fallback to cached data if available
            if self._cached_data is not None:
                print(f"[WARNING] Weather API failed, using cached data: {e}")
                return self._cached_data

            # Ultimate fallback - assume clear sky
            print(f"[ERROR] Weather API failed, no cache available: {e}")
            return {
                "cloud_cover_pct": 0,
                "timestamp": int(time.time()),
                "fallback": True
            }

    def _fetch_from_api(self) -> Dict[str, any]:
        """Fetch weather data from OpenWeatherMap API"""
        params = {
            "lat": self.lat,
            "lon": self.lon,
            "appid": self.api_key,
            "units": "metric"
        }

        response = requests.get(self.base_url, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()

        return {
            "cloud_cover_pct": data.get("clouds", {}).get("all", 0),
            "timestamp": int(time.time()),
            "weather_description": data.get("weather", [{}])[0].get("description", "unknown"),
            "temperature_c": data.get("main", {}).get("temp", 0),
            "fallback": False
        }

    def _update_cache(self, data: Dict):
        """Update the cache with fresh data"""
        self._cached_data = data
        self._cache_timestamp = time.time()

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if self._cached_data is None:
            return False

        age = time.time() - self._cache_timestamp
        return age < self.cache_ttl

    def force_refresh(self) -> Dict[str, any]:
        """Force a refresh of weather data, bypassing cache"""
        self._cache_timestamp = 0
        return self.get_cloud_cover()


if __name__ == "__main__":
    # Test the weather service
    service = WeatherService()

    print("Testing Weather Service...")
    print("=" * 50)

    # First call (from API)
    data = service.get_cloud_cover()
    print(f"Cloud Cover: {data['cloud_cover_pct']}%")
    print(f"Description: {data.get('weather_description', 'N/A')}")
    print(f"Temperature: {data.get('temperature_c', 'N/A')}°C")
    print(f"Fallback Mode: {data.get('fallback', False)}")
    print(f"Timestamp: {data['timestamp']}")

    # Second call (from cache)
    print("\n" + "=" * 50)
    print("Second call (should use cache)...")
    data2 = service.get_cloud_cover()
    print(f"Cloud Cover: {data2['cloud_cover_pct']}%")
    print(f"Cache was used: {data['timestamp'] == data2['timestamp']}")
