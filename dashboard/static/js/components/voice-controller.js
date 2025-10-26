/**
 * Voice Controller - Connects Voice Visualizer with Gemini Chat
 * Handles UI interactions and coordinates between visualizer and Gemini
 */

class VoiceController {
    constructor() {
        // Components
        this.visualizer = null;
        this.gemini = null;

        // UI Elements
        this.overlay = document.getElementById('voiceVisualizerOverlay');
        this.toggleBtn = document.getElementById('toggleVoiceVisualizer');
        this.closeBtn = document.getElementById('closeVoiceVisualizer');

        this.isActive = false;

        this.init();
    }

    init() {
        // Initialize components
        this.visualizer = new VoiceVisualizer('voiceVisualizerCanvas');
        this.gemini = new GeminiVoiceIntegrated();
        this.gemini.setVisualizer(this.visualizer);

        // Event listeners
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => this.handleToggle());
        }

        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.handleClose());
        }

        // Keyboard shortcut (Escape to close)
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isActive) {
                this.handleClose();
            }
        });

        console.log('[VoiceController] Initialized');
    }

    async handleToggle() {
        if (this.isActive) {
            this.handleClose();
        } else {
            await this.handleOpen();
        }
    }

    async handleOpen() {
        try {
            console.log('[VoiceController] Opening voice assistant...');

            // Show overlay
            this.overlay.classList.add('active');

            // Start visualizer (this gets microphone access)
            await this.visualizer.start();

            // Start Gemini with the visualizer's audio context and stream
            const stream = this.visualizer.microphone.mediaStream;
            const audioContext = this.visualizer.audioContext;

            await this.gemini.start(stream, audioContext);

            this.isActive = true;

            console.log('[VoiceController] Voice assistant activated');

        } catch (error) {
            console.error('[VoiceController] Failed to open:', error);
            this.handleClose();
            alert('Failed to start voice assistant. Please check microphone permissions.');
        }
    }

    handleClose() {
        console.log('[VoiceController] Closing voice assistant...');

        // Stop Gemini first
        if (this.gemini) {
            this.gemini.stop();
        }

        // Stop visualizer
        if (this.visualizer) {
            this.visualizer.stop();
        }

        // Hide overlay
        this.overlay.classList.remove('active');

        this.isActive = false;

        console.log('[VoiceController] Voice assistant closed');
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.voiceController = new VoiceController();
    });
} else {
    window.voiceController = new VoiceController();
}

console.log('[VoiceController] Component loaded');
