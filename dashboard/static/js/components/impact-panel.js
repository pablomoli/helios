// Impact Panel Component
class ImpactPanel {
    constructor() {
        this.impactEnergy = document.getElementById('impactEnergy');
        this.impactCost = document.getElementById('impactCost');
        this.impactCO2 = document.getElementById('impactCO2');
    }

    update(data) {
        const energy = data.energy_kWh || 0;
        this.impactEnergy.textContent = energy.toFixed(6);

        const cost = data.usd_saved || 0;
        this.impactCost.textContent = `$${cost.toFixed(4)}`;

        const co2 = data.co2_g || 0;
        this.impactCO2.textContent = co2.toFixed(2);
    }
}

const impactPanel = new ImpactPanel();
