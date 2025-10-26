/**
 * AI Voice Interface Component
 * Displays wake word detection status and audio spectrogram visualization
 */

class AIVoiceInterface {
    constructor() {
        this.canvas = document.getElementById('spectrogramCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.wakeWordStatus = document.getElementById('wakeWordStatus');
        this.aiResponse = document.getElementById('aiResponse');

        // Spectrogram data
        this.spectrogramData = [];
        this.maxDataPoints = 100;
        this.frequencyBands = 32;

        // Wake word state
        this.isActive = false;
        this.lastActivation = 0;

        // Audio setup
        this.mediaRecorder = null;
        this.audioContext = null;
        this.analyser = null;
        this.microphone = null;
        this.isListening = false;
        this.audioChunks = [];

        // Colors
        this.colors = {
            inactive: '#4a5568',
            active: '#48bb78',
            speaking: '#ed8936'
        };

        this.init();
    }

    init() {
        // Set canvas size
        this.resizeCanvas();

        // Start animation loop
        this.animate();

        // Listen for window resize
        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth || 400;
        this.canvas.height = 120;
    }

    /**
     * Generate audio spectrum data from real microphone input or simulated
     */
    generateSpectrumData() {
        if (this.analyser && this.isListening) {
            // Use real audio data from microphone
            const bufferLength = this.analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            this.analyser.getByteFrequencyData(dataArray);

            // Convert to normalized spectrum for our frequency bands
            const spectrum = [];
            const step = Math.floor(bufferLength / this.frequencyBands);

            for (let i = 0; i < this.frequencyBands; i++) {
                const start = i * step;
                const end = start + step;
                let sum = 0;

                for (let j = start; j < end && j < bufferLength; j++) {
                    sum += dataArray[j];
                }

                const amplitude = (sum / step) / 255; // Normalize to 0-1
                spectrum.push(amplitude);
            }

            return spectrum;
        } else {
            // Fallback to simulated data
            const spectrum = [];
            const time = Date.now() / 1000;

            for (let i = 0; i < this.frequencyBands; i++) {
                let amplitude = Math.random() * 0.3;

                if (this.isActive && Date.now() - this.lastActivation < 3000) {
                    const speechPattern = Math.sin(time * 3 + i * 0.5) * 0.4 + 0.5;
                    amplitude = Math.max(amplitude, speechPattern);
                }

                spectrum.push(amplitude);
            }

            return spectrum;
        }
    }

    /**
     * Start using real audio from microphone
     */
    startRealAudio(analyser) {
        this.analyser = analyser;
        this.isListening = true;
    }

    /**
     * Stop using real audio
     */
    stopRealAudio() {
        this.analyser = null;
        this.isListening = false;
    }

    /**
     * Update spectrogram with new audio data
     */
    updateSpectrogram(spectrum) {
        // Add new spectrum to the beginning
        this.spectrogramData.unshift(spectrum);

        // Keep only max data points
        if (this.spectrogramData.length > this.maxDataPoints) {
            this.spectrogramData.pop();
        }
    }

    /**
     * Draw spectrogram visualization
     */
    drawSpectrogram() {
        const ctx = this.ctx;
        const width = this.canvas.width;
        const height = this.canvas.height;

        // Clear canvas
        ctx.fillStyle = '#1a202c';
        ctx.fillRect(0, 0, width, height);

        if (this.spectrogramData.length === 0) return;

        const columnWidth = width / this.maxDataPoints;
        const barHeight = height / this.frequencyBands;

        // Draw spectrogram columns (right to left, newest to oldest)
        for (let col = 0; col < this.spectrogramData.length; col++) {
            const spectrum = this.spectrogramData[col];
            const x = width - (col + 1) * columnWidth;

            for (let row = 0; row < spectrum.length; row++) {
                const amplitude = spectrum[row];
                const y = height - (row + 1) * barHeight;

                // Color based on amplitude
                const hue = this.isActive ? 140 : 200; // Green if active, blue if inactive
                const saturation = 70;
                const lightness = 20 + amplitude * 60;

                ctx.fillStyle = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
                ctx.fillRect(x, y, columnWidth - 1, barHeight - 1);
            }
        }

        // Draw frequency grid lines
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = (height / 4) * i;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }
    }

    /**
     * Activate wake word detection
     */
    activateWakeWord(query = '') {
        this.isActive = true;
        this.lastActivation = Date.now();

        const indicator = this.wakeWordStatus.querySelector('.status-indicator');
        const statusText = this.wakeWordStatus.querySelector('.status-text');

        indicator.classList.remove('inactive');
        indicator.classList.add('active');
        statusText.textContent = query || 'Wake word detected!';

        // Auto-deactivate after 5 seconds
        setTimeout(() => this.deactivateWakeWord(), 5000);
    }

    /**
     * Deactivate wake word detection
     */
    deactivateWakeWord() {
        this.isActive = false;

        const indicator = this.wakeWordStatus.querySelector('.status-indicator');
        const statusText = this.wakeWordStatus.querySelector('.status-text');

        indicator.classList.remove('active');
        indicator.classList.add('inactive');
        statusText.textContent = 'Listening for "Helios"...';
    }

    /**
     * Update AI response display
     */
    updateResponse(response) {
        const responseDiv = this.aiResponse.querySelector('.response-text');
        responseDiv.textContent = response;

        // Add animation
        responseDiv.style.animation = 'none';
        setTimeout(() => {
            responseDiv.style.animation = 'fadeIn 0.5s ease';
        }, 10);
    }

    /**
     * Animation loop
     */
    animate() {
        // Generate and update spectrogram data
        const spectrum = this.generateSpectrumData();
        this.updateSpectrogram(spectrum);

        // Draw
        this.drawSpectrogram();

        // Continue animation
        requestAnimationFrame(() => this.animate());
    }

    /**
     * Handle voice query event from WebSocket
     */
    handleVoiceQuery(data) {
        if (data.query) {
            this.activateWakeWord(data.query);
        }
    }

    /**
     * Handle voice response event from WebSocket
     */
    handleVoiceResponse(data) {
        if (data.response) {
            this.updateResponse(data.response);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.aiVoiceInterface = new AIVoiceInterface();

    // Listen for WebSocket events
    if (window.socket) {
        window.socket.on('voice_query', (data) => {
            window.aiVoiceInterface.handleVoiceQuery(data);
        });

        window.socket.on('voice_response', (data) => {
            window.aiVoiceInterface.handleVoiceResponse(data);
        });

        window.socket.on('voice_log', (data) => {
            if (data.type === 'query') {
                window.aiVoiceInterface.activateWakeWord(data.text);
            } else if (data.type === 'response') {
                window.aiVoiceInterface.updateResponse(data.text);
            }
        });
    }
});
