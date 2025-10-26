// Voice Visualizer - Alexa-style waveform animation
// Uses Web Audio API for real-time microphone analysis
class VoiceVisualizer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.warn('[VoiceVisualizer] Canvas not found:', canvasId);
            return;
        }

        this.ctx = this.canvas.getContext('2d');
        this.audioContext = null;
        this.analyser = null;
        this.microphone = null;
        this.dataArray = null;
        this.bufferLength = 0;
        this.animationId = null;
        this.isActive = false;
        this.isListening = false;

        // Visual settings
        this.barCount = 60; // Number of bars in the waveform
        this.barColor = '#00D9FF'; // Cyan color
        this.barColorActive = '#FFB800'; // Gold when speaking
        this.backgroundColor = 'rgba(10, 14, 26, 0.95)';

        // Resize canvas to match display size
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());

        console.log('[VoiceVisualizer] Initialized');
    }

    resizeCanvas() {
        if (!this.canvas) return;

        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * window.devicePixelRatio;
        this.canvas.height = rect.height * window.devicePixelRatio;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        this.width = rect.width;
        this.height = rect.height;
    }

    async start() {
        if (this.isActive) {
            console.log('[VoiceVisualizer] Already active');
            return;
        }

        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // Create audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            this.microphone = this.audioContext.createMediaStreamSource(stream);

            // Configure analyser
            this.analyser.fftSize = 256;
            this.bufferLength = this.analyser.frequencyBinCount;
            this.dataArray = new Uint8Array(this.bufferLength);

            // Connect microphone to analyser
            this.microphone.connect(this.analyser);

            this.isActive = true;
            this.isListening = true;
            this.animate();

            console.log('[VoiceVisualizer] Started successfully');
        } catch (error) {
            console.error('[VoiceVisualizer] Failed to start:', error);
            alert('Microphone access denied. Please allow microphone access to use voice features.');
        }
    }

    stop() {
        if (!this.isActive) return;

        // Stop animation
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }

        // Stop microphone
        if (this.microphone && this.microphone.mediaStream) {
            this.microphone.mediaStream.getTracks().forEach(track => track.stop());
        }

        // Close audio context
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        this.isActive = false;
        this.isListening = false;

        // Clear canvas
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(0, 0, this.width, this.height);

        console.log('[VoiceVisualizer] Stopped');
    }

    toggle() {
        if (this.isActive) {
            this.stop();
        } else {
            this.start();
        }
    }

    setListening(listening) {
        this.isListening = listening;
    }

    animate() {
        if (!this.isActive) return;

        this.animationId = requestAnimationFrame(() => this.animate());

        // Get frequency data
        this.analyser.getByteFrequencyData(this.dataArray);

        // Clear canvas
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(0, 0, this.width, this.height);

        // Calculate bar dimensions
        const barWidth = this.width / this.barCount;
        const centerY = this.height / 2;
        const maxBarHeight = this.height * 0.8;

        // Draw waveform bars
        for (let i = 0; i < this.barCount; i++) {
            // Sample frequency data (spread across the frequency range)
            const dataIndex = Math.floor((i / this.barCount) * this.bufferLength);
            const value = this.dataArray[dataIndex];

            // Normalize value (0-1)
            const normalizedValue = value / 255;

            // Calculate bar height with smooth easing
            const barHeight = normalizedValue * maxBarHeight;

            // Add some minimum height for visual interest
            const minHeight = 4;
            const finalHeight = Math.max(barHeight, minHeight);

            // Calculate position
            const x = i * barWidth;
            const y = centerY - finalHeight / 2;

            // Create gradient for each bar
            const gradient = this.ctx.createLinearGradient(x, y, x, y + finalHeight);

            // Color changes based on listening state
            if (this.isListening && normalizedValue > 0.1) {
                // Active/speaking - gold gradient
                gradient.addColorStop(0, this.barColorActive);
                gradient.addColorStop(1, 'rgba(255, 184, 0, 0.3)');
            } else {
                // Idle - cyan gradient
                gradient.addColorStop(0, this.barColor);
                gradient.addColorStop(1, 'rgba(0, 217, 255, 0.3)');
            }

            // Draw bar with rounded corners
            this.ctx.fillStyle = gradient;
            this.ctx.beginPath();

            const radius = barWidth * 0.3;
            const barWidthActual = barWidth * 0.7; // Leave gap between bars

            // Rounded rectangle
            this.ctx.moveTo(x + radius, y);
            this.ctx.lineTo(x + barWidthActual - radius, y);
            this.ctx.quadraticCurveTo(x + barWidthActual, y, x + barWidthActual, y + radius);
            this.ctx.lineTo(x + barWidthActual, y + finalHeight - radius);
            this.ctx.quadraticCurveTo(x + barWidthActual, y + finalHeight, x + barWidthActual - radius, y + finalHeight);
            this.ctx.lineTo(x + radius, y + finalHeight);
            this.ctx.quadraticCurveTo(x, y + finalHeight, x, y + finalHeight - radius);
            this.ctx.lineTo(x, y + radius);
            this.ctx.quadraticCurveTo(x, y, x + radius, y);
            this.ctx.closePath();

            this.ctx.fill();

            // Add glow effect for active bars
            if (normalizedValue > 0.3) {
                this.ctx.shadowBlur = 15;
                this.ctx.shadowColor = this.isListening ? this.barColorActive : this.barColor;
                this.ctx.fill();
                this.ctx.shadowBlur = 0;
            }
        }
    }
}

// Export for use in other components
window.VoiceVisualizer = VoiceVisualizer;

console.log('[VoiceVisualizer] Component loaded');