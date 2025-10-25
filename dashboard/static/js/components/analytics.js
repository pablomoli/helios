// Analytics Component with Smooth Animations
class Analytics {
    constructor() {
        this.currentPower = document.getElementById('currentPower');
        this.energyToday = document.getElementById('energyToday');
        this.currentMode = document.getElementById('currentMode');
        this.panelVoltage = document.getElementById('panelVoltage');
        this.panelCurrent = document.getElementById('panelCurrent');

        this.accumulatedEnergy = 0;
        this.lastUpdateTime = Date.now();
    }

    addFlashEffect(element) {
        element.classList.add('value-update');
        setTimeout(() => element.classList.remove('value-update'), 500);
    }

    updateSensorData(data) {
        const power = data.panel_power_mW || 0;
        this.currentPower.textContent = `${power.toFixed(1)} mW`;
        this.addFlashEffect(this.currentPower);

        const voltage = data.panel_voltage_V || 0;
        this.panelVoltage.textContent = `${voltage.toFixed(2)} V`;

        const current = data.panel_current_mA || 0;
        this.panelCurrent.textContent = `${current.toFixed(1)} mA`;

        // Accumulate energy
        const now = Date.now();
        const timeDelta = (now - this.lastUpdateTime) / 1000 / 3600; // hours
        this.accumulatedEnergy += power * timeDelta;
        this.lastUpdateTime = now;

        this.energyToday.textContent = `${this.accumulatedEnergy.toFixed(1)} mWh`;
        this.addFlashEffect(this.energyToday);
    }

    updateStatusData(data) {
        const mode = data.mode || '--';
        if (this.currentMode.textContent !== mode) {
            this.currentMode.textContent = mode;
            this.addFlashEffect(this.currentMode);
        }

        // Update sky map with cloud cover
        if (skyMap && data.cloud_cover_pct !== undefined) {
            skyMap.update({ cloud_cover_pct: data.cloud_cover_pct });
        }
    }
}

const analytics = new Analytics();
