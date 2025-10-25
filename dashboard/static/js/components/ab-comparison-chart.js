// A/B Comparison Chart Component
class ABComparisonChart {
    constructor() {
        this.ctx = document.getElementById('performanceChart').getContext('2d');
        this.deltaBadge = document.getElementById('deltaBadge');

        this.data = {
            labels: [],
            actual: [],
            shadow: []
        };

        this.maxDataPoints = 20;

        this.chart = new Chart(this.ctx, {
            type: 'line',
            data: {
                labels: this.data.labels,
                datasets: [
                    {
                        label: 'Predictive Mode',
                        data: this.data.actual,
                        borderColor: '#00D9FF',
                        backgroundColor: 'rgba(0, 217, 255, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Reactive Mode',
                        data: this.data.shadow,
                        borderColor: '#FDB813',
                        backgroundColor: 'rgba(253, 184, 19, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffffff'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#9ba3af' },
                        grid: { color: '#2d3748' }
                    },
                    y: {
                        ticks: { color: '#9ba3af' },
                        grid: { color: '#2d3748' },
                        title: {
                            display: true,
                            text: 'Power (mW)',
                            color: '#ffffff'
                        }
                    }
                }
            }
        });
    }

    update(data) {
        const timestamp = new Date(data.timestamp * 1000).toLocaleTimeString();

        // Add new data point
        this.data.labels.push(timestamp);
        this.data.actual.push(data.actual_strategy_power_mW);
        this.data.shadow.push(data.shadow_strategy_power_mW);

        // Keep only last N points
        if (this.data.labels.length > this.maxDataPoints) {
            this.data.labels.shift();
            this.data.actual.shift();
            this.data.shadow.shift();
        }

        // Update chart
        this.chart.update();

        // Update delta badge
        const delta = data.delta_pct || 0;
        const deltaValue = this.deltaBadge.querySelector('.delta-value');
        deltaValue.textContent = `${delta >= 0 ? '+' : ''}${delta.toFixed(1)}%`;

        // Update badge color
        if (delta >= 0) {
            this.deltaBadge.classList.remove('negative');
        } else {
            this.deltaBadge.classList.add('negative');
        }
    }
}

let abChart = null;

// Initialize chart after DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    abChart = new ABComparisonChart();
});
