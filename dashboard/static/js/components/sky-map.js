// Sky Map Component with Live Cloud Coverage
// SECURITY: Uses backend proxy endpoints - no API keys exposed to frontend
class SkyMap {
    constructor() {
        this.cloudValue = document.getElementById('cloudValue');
        this.locationDisplay = document.getElementById('locationDisplay');
        this.map = null;
        this.cloudLayer = null;
        this.marker = null;
        this.userLat = null;
        this.userLon = null;
        this.defaultLat = null;
        this.defaultLon = null;

        this.init();
    }

    async init() {
        // Get default location from backend
        await this.fetchConfig();

        // Get user location
        await this.getUserLocation();

        // Initialize map
        this.initializeMap();
    }

    async fetchConfig() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();
            this.defaultLat = config.default_lat;
            this.defaultLon = config.default_lon;
        } catch (error) {
            console.error('[SkyMap] Failed to fetch config:', error);
            // Fallback to San Francisco
            this.defaultLat = 37.7749;
            this.defaultLon = -122.4194;
        }
    }

    async getUserLocation() {
        return new Promise((resolve) => {
            if ('geolocation' in navigator) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        this.userLat = position.coords.latitude;
                        this.userLon = position.coords.longitude;
                        console.log(`[SkyMap] User location: ${this.userLat}, ${this.userLon}`);
                        this.updateLocationDisplay(this.userLat, this.userLon);
                        resolve();
                    },
                    (error) => {
                        console.warn('[SkyMap] Geolocation denied, using default location');
                        this.userLat = this.defaultLat;
                        this.userLon = this.defaultLon;
                        this.updateLocationDisplay(this.userLat, this.userLon, true);
                        resolve();
                    }
                );
            } else {
                console.warn('[SkyMap] Geolocation not available');
                this.userLat = this.defaultLat;
                this.userLon = this.defaultLon;
                this.updateLocationDisplay(this.userLat, this.userLon, true);
                resolve();
            }
        });
    }

    async updateLocationDisplay(lat, lon, isDefault = false) {
        const locationText = this.locationDisplay.querySelector('.location-text');

        if (isDefault) {
            locationText.textContent = 'Using default location';
            return;
        }

        // Show loading state
        locationText.textContent = 'Loading location...';

        try {
            // Reverse geocoding via secure backend proxy
            const response = await fetch(`/api/geocode/reverse?lat=${lat}&lon=${lon}`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('[SkyMap] Geocoding result:', result);

            if (result.source && result.data) {
                // Backend proxy returned data successfully
                if (result.data.name) {
                    const location = result.data;
                    const cityName = location.name;
                    const state = location.state ? `, ${location.state}` : '';
                    const country = location.country ? ` ${location.country}` : '';
                    locationText.textContent = `${cityName}${state}${country}`;
                    console.log(`[SkyMap] Location set to: ${cityName}${state}${country}`);
                    return;
                }
            }

            // Fallback to coordinates if no location name found
            console.warn('[SkyMap] No location name found, showing coordinates');
            locationText.textContent = `${lat.toFixed(4)}°, ${lon.toFixed(4)}°`;

        } catch (error) {
            console.error('[SkyMap] Failed to get location name:', error);
            // Fallback to coordinates on error
            locationText.textContent = `${lat.toFixed(4)}°, ${lon.toFixed(4)}°`;
        }
    }

    initializeMap() {
        if (!this.userLat || !this.userLon) {
            console.error('[SkyMap] Missing required data for map initialization');
            return;
        }

        // Create map centered on user location
        this.map = L.map('cloudMap', {
            center: [this.userLat, this.userLon],
            zoom: 10,
            zoomControl: true,
            attributionControl: true
        });

        // Add base tile layer (dark theme) - No API key required
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(this.map);

        // Add cloud coverage overlay via secure backend proxy
        this.cloudLayer = L.tileLayer(
            '/api/tiles/clouds/{z}/{x}/{y}.png',
            {
                attribution: 'Cloud data &copy; <a href="https://openweathermap.org">OpenWeatherMap</a>',
                opacity: 0.7,
                maxZoom: 19
            }
        ).addTo(this.map);

        // Add marker for current location
        const sunIcon = L.divIcon({
            className: 'custom-sun-marker',
            html: '<div style="font-size: 24px; text-shadow: 0 0 10px rgba(253,184,19,0.8);">☀️</div>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });

        this.marker = L.marker([this.userLat, this.userLon], { icon: sunIcon })
            .addTo(this.map)
            .bindPopup('Your Solar Tracker Location');

        console.log('[SkyMap] Map initialized successfully');
    }

    update(data) {
        const cloudCover = data.cloud_cover_pct || 0;
        this.cloudValue.textContent = `${cloudCover}%`;
    }

    refreshCloudLayer() {
        if (this.cloudLayer && this.map) {
            // Remove old layer
            this.map.removeLayer(this.cloudLayer);

            // Add fresh layer via backend proxy with cache buster
            this.cloudLayer = L.tileLayer(
                `/api/tiles/clouds/{z}/{x}/{y}.png?t=${Date.now()}`,
                {
                    attribution: 'Cloud data &copy; <a href="https://openweathermap.org">OpenWeatherMap</a>',
                    opacity: 0.7,
                    maxZoom: 19
                }
            ).addTo(this.map);

            console.log('[SkyMap] Cloud layer refreshed');
        }
    }
}

let skyMap = null;

// Initialize after DOM and Leaflet are ready
document.addEventListener('DOMContentLoaded', () => {
    skyMap = new SkyMap();

    // Refresh cloud layer every 10 minutes
    setInterval(() => {
        if (skyMap) {
            skyMap.refreshCloudLayer();
        }
    }, 600000); // 10 minutes
});
