// Safety Monitor Component
class SafetyMonitor {
    constructor() {
        this.safetyStatus = document.getElementById('safetyStatus');
        this.servoStatus = document.getElementById('servoStatus');
        this.angleCheck = document.getElementById('angleCheck');
        this.temperature = document.getElementById('temperature');
    }

    update(data) {
        const statusIcon = this.safetyStatus.querySelector('.status-icon use');
        const statusText = this.safetyStatus.querySelector('.status-text');

        // Update servo status
        this.servoStatus.textContent = data.servo_status || 'normal';

        // Update angle check
        const angleViolation = data.angle_violation || false;
        this.angleCheck.textContent = angleViolation ? 'VIOLATION' : 'OK';
        this.angleCheck.style.color = angleViolation ? '#ef4444' : '#10b981';

        // Update temperature
        const temp = data.temperature_C || 0;
        this.temperature.textContent = `${temp.toFixed(1)}°C`;

        // Determine overall status
        const isNormal = data.servo_status === 'normal' && !angleViolation && temp < 50;

        if (isNormal) {
            this.safetyStatus.classList.remove('alert');
            statusIcon.setAttribute('href', '#icon-check');
            statusText.textContent = 'Normal';
        } else {
            this.safetyStatus.classList.add('alert');
            statusIcon.setAttribute('href', '#icon-warning');
            statusText.textContent = 'Alert';
        }
    }
}

const safetyMonitor = new SafetyMonitor();
