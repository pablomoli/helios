// WebSocket Connection Manager
class ConnectionManager {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 2000;
        this.eventHandlers = {};
    }

    connect() {
        console.log('[ConnectionManager] Connecting to server...');
        this.socket = io();

        this.socket.on('connect', () => {
            this.connected = true;
            this.reconnectAttempts = 0;
            console.log('[ConnectionManager] Connected successfully');
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', () => {
            this.connected = false;
            console.log('[ConnectionManager] Disconnected from server');
            this.updateConnectionStatus(false);
            this.attemptReconnect();
        });

        this.socket.on('connection_status', (data) => {
            console.log('[ConnectionManager] Connection status:', data);
        });

        // Data event handlers
        this.socket.on('sensor_data', (data) => {
            this.emit('sensor_data', data);
        });

        this.socket.on('status_data', (data) => {
            this.emit('status_data', data);
        });

        this.socket.on('performance_delta', (data) => {
            this.emit('performance_delta', data);
        });

        this.socket.on('impact_data', (data) => {
            this.emit('impact_data', data);
        });

        this.socket.on('safety_data', (data) => {
            this.emit('safety_data', data);
        });
    }

    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('[ConnectionManager] Max reconnect attempts reached');
            return;
        }

        this.reconnectAttempts++;
        console.log(`[ConnectionManager] Reconnecting... (Attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            if (!this.connected) {
                this.connect();
            }
        }, this.reconnectDelay * this.reconnectAttempts);
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        const dot = statusElement.querySelector('.status-dot');
        const text = statusElement.querySelector('.status-text');

        if (connected) {
            dot.classList.add('connected');
            text.textContent = 'Connected';
        } else {
            dot.classList.remove('connected');
            text.textContent = 'Disconnected';
        }
    }

    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }

    emit(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => handler(data));
        }
    }

    requestData(topic = 'all') {
        if (this.connected && this.socket) {
            this.socket.emit('request_data', { topic });
        }
    }
}

// Global connection manager instance
const connectionManager = new ConnectionManager();
