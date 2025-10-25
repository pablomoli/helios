// Sky Map Component with Live Cloud Coverage
class SkyMap {
    constructor() {
        this.cloudValue = document.getElementById('cloudValue');
        this.locationDisplay = document.getElementById('locationDisplay');
        this.map = null;
        this.cloudLayer = null;
        this.marker = null;
        this.apiKey = null;
        this.userLat = null;
        this.userLon = null;

        this.init();
    }

    async init() {
        // Get API key from backend
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
            this.apiKey = config.openweather_api_key;
            this.defaultLat = config.default_lat;
            this.defaultLon = config.default_lon;
        } catch (error) {
            console.error('[SkyMap] Failed to fetch config:', error);
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

        try {
            // Reverse geocoding to get location name
            const response = await fetch(
                `https://api.openweathermap.org/geo/1.0/reverse?lat=${lat}&lon=${lon}&limit=1&appid=${this.apiKey}`
            );
            const data = await response.json();

            if (data && data.length > 0) {
                const location = data[0];
                const cityName = location.name;
                const state = location.state ? `, ${location.state}` : '';
                locationText.textContent = `${cityName}${state}`;
            } else {
                locationText.textContent = `${lat.toFixed(2)}°, ${lon.toFixed(2)}°`;
            }
        } catch (error) {
            console.error('[SkyMap] Failed to get location name:', error);
            locationText.textContent = `${lat.toFixed(2)}°, ${lon.toFixed(2)}°`;
        }
    }

    initializeMap() {
        if (!this.userLat || !this.userLon || !this.apiKey) {
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

        // Add base tile layer (dark theme)
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(this.map);

        // Add cloud coverage overlay from OpenWeatherMap
        this.cloudLayer = L.tileLayer(
            `https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid=${this.apiKey}`,
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

        // Optionally refresh cloud layer every 10 minutes
        // OpenWeatherMap updates cloud data periodically
    }

    refreshCloudLayer() {
        if (this.cloudLayer && this.map) {
            this.map.removeLayer(this.cloudLayer);
            this.cloudLayer = L.tileLayer(
                `https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid=${this.apiKey}&t=${Date.now()}`,
                {
                    attribution: 'Cloud data &copy; <a href="https://openweathermap.org">OpenWeatherMap</a>',
                    opacity: 0.7,
                    maxZoom: 19
                }
            ).addTo(this.map);
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
