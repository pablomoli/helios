// Main Application Entry Point
console.log('[Helios AI] Dashboard initializing...');

// Initialize connection
connectionManager.connect();

// Register event handlers
connectionManager.on('sensor_data', (data) => {
    analytics.updateSensorData(data);
});

connectionManager.on('status_data', (data) => {
    analytics.updateStatusData(data);
});

connectionManager.on('performance_delta', (data) => {
    if (abChart) {
        abChart.update(data);
    }
});

connectionManager.on('impact_data', (data) => {
    impactPanel.update(data);
});

connectionManager.on('safety_data', (data) => {
    safetyMonitor.update(data);
});

// Initial data request
setTimeout(() => {
    connectionManager.requestData('all');
}, 1000);

console.log('[Helios AI] Dashboard ready');
