// Impact Panel Component with Smooth Counter Animations
class ImpactPanel {
    constructor() {
        this.impactEnergy = document.getElementById('impactEnergy');
        this.impactCost = document.getElementById('impactCost');
        this.impactCO2 = document.getElementById('impactCO2');

        // Store previous values for smooth transitions
        this.prevEnergy = 0;
        this.prevCost = 0;
        this.prevCO2 = 0;
    }

    animateValue(element, start, end, duration, decimals, prefix = '', suffix = '') {
        if (!element) return;  // Guard against missing elements

        // Cancel any existing animation for this element
        if (element.__animateState) {
            if (element.__animateState.rafId) {
                cancelAnimationFrame(element.__animateState.rafId);
            }
            if (element.__animateState.flashTimeoutId) {
                clearTimeout(element.__animateState.flashTimeoutId);
            }
        }

        // Initialize animation state object on the element
        element.__animateState = {
            rafId: null,
            flashTimeoutId: null
        };

        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function for smooth animation
            const easeOutCubic = progress => 1 - Math.pow(1 - progress, 3);
            const easedProgress = easeOutCubic(progress);

            const current = start + (end - start) * easedProgress;
            element.textContent = `${prefix}${current.toFixed(decimals)}${suffix}`;

            // Add flash effect only once at the start
            if (elapsed < 50 && !element.classList.contains('value-update')) {
                element.classList.add('value-update');
                
                // Clear any existing flash timeout and set new one
                if (element.__animateState.flashTimeoutId) {
                    clearTimeout(element.__animateState.flashTimeoutId);
                }
                
                element.__animateState.flashTimeoutId = setTimeout(() => {
                    element.classList.remove('value-update');
                    if (element.__animateState) {
                        element.__animateState.flashTimeoutId = null;
                    }
                }, 500);
            }

            if (progress < 1) {
                element.__animateState.rafId = requestAnimationFrame(animate);
            } else {
                // Animation complete, clear the RAF id
                if (element.__animateState) {
                    element.__animateState.rafId = null;
                }
            }
        };

        element.__animateState.rafId = requestAnimationFrame(animate);
    }

    update(data) {
        const energy = data.energy_kWh || 0;
        const cost = data.usd_saved || 0;
        const co2 = data.co2_g || 0;

        // Animate energy value
        if (Math.abs(energy - this.prevEnergy) > 0.000001) {
            this.animateValue(this.impactEnergy, this.prevEnergy, energy, 500, 6);
            this.prevEnergy = energy;
        }

        // Animate cost value
        if (Math.abs(cost - this.prevCost) > 0.0001) {
            this.animateValue(this.impactCost, this.prevCost, cost, 500, 4, '$');
            this.prevCost = cost;
        }

        // Animate CO2 value
        if (Math.abs(co2 - this.prevCO2) > 0.01) {
            this.animateValue(this.impactCO2, this.prevCO2, co2, 500, 2);
            this.prevCO2 = co2;
        }
    }
}

const impactPanel = new ImpactPanel();
