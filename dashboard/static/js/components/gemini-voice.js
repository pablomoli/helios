/**
 * Gemini Voice Chat Component
 * Integrates with the dashboard's voice assistant panel
 */

class GeminiVoiceChat {
    constructor() {
        this.streamer = null;
        this.isActive = false;

        // DOM elements
        this.startBtn = document.getElementById('startVoiceBtn');
        this.stopBtn = document.getElementById('stopVoiceBtn');
        this.statusIndicator = document.querySelector('.voice-status-indicator');
        this.statusText = document.querySelector('.voice-status-text');
        this.voiceLog = document.getElementById('voiceLog');

        // WebSocket URL (same origin as dashboard)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.wsUrl = `${protocol}//${window.location.host}/ws/gemini-voice`;

        this.init();
    }

    init() {
        // Event listeners
        this.startBtn.addEventListener('click', () => this.startChat());
        this.stopBtn.addEventListener('click', () => this.stopChat());

        // Keyboard shortcut (Ctrl+Space)
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.code === 'Space') {
                e.preventDefault();
                if (!this.isActive) {
                    this.startChat();
                } else {
                    this.stopChat();
                }
            }
        });

        console.log('[Gemini Voice] Component initialized');
    }

    async startChat() {
        try {
            this.logMessage('system', 'Connecting to Gemini...');

            // Create audio streamer
            this.streamer = new AudioStreamer(this.wsUrl);

            // Set up callbacks
            this.streamer.onStatusChange = (status) => {
                this.updateStatus(status);

                if (status === 'connected') {
                    this.logMessage('system', 'Connected! You can start talking.');
                } else if (status === 'connecting') {
                    this.logMessage('system', 'Connecting...');
                } else if (status === 'disconnected') {
                    this.logMessage('system', 'Disconnected.');
                }
            };

            this.streamer.onSpeakingChange = (speaking) => {
                if (speaking) {
                    this.statusIndicator.classList.add('speaking');
                    this.logMessage('user', 'Listening...');
                } else {
                    this.statusIndicator.classList.remove('speaking');
                }
            };

            this.streamer.onError = (error) => {
                this.logMessage('error', `Error: ${error}`);
                this.stopChat();
            };

            // Update UI
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
            this.isActive = true;

            // Connect
            await this.streamer.connect();

        } catch (error) {
            console.error('[Gemini Voice] Start error:', error);
            this.logMessage('error', `Failed to start: ${error.message}`);
            this.stopChat();
        }
    }

    stopChat() {
        if (this.streamer) {
            this.streamer.disconnect();
            this.streamer = null;
        }

        // Update UI
        this.startBtn.disabled = false;
        this.stopBtn.disabled = true;
        this.isActive = false;

        this.updateStatus('disconnected');
        this.logMessage('system', 'Voice chat ended.');
    }

    updateStatus(status) {
        // Update status indicator
        this.statusIndicator.className = 'voice-status-indicator';

        switch (status) {
            case 'connected':
                this.statusIndicator.classList.add('connected');
                this.statusText.textContent = 'Connected';
                break;
            case 'connecting':
                this.statusIndicator.classList.add('connecting');
                this.statusText.textContent = 'Connecting...';
                break;
            case 'disconnected':
                this.statusIndicator.classList.add('disconnected');
                this.statusText.textContent = 'Disconnected';
                break;
            case 'error':
                this.statusIndicator.classList.add('error');
                this.statusText.textContent = 'Error';
                break;
            default:
                this.statusText.textContent = 'Ready';
        }
    }

    logMessage(type, text) {
        const entry = document.createElement('div');
        entry.className = `voice-entry ${type}`;

        const time = document.createElement('span');
        time.className = 'voice-time';
        time.textContent = this.getCurrentTime();

        const message = document.createElement('span');
        message.className = 'voice-text';
        message.textContent = text;

        entry.appendChild(time);
        entry.appendChild(message);

        this.voiceLog.appendChild(entry);

        // Auto-scroll to bottom
        this.voiceLog.scrollTop = this.voiceLog.scrollHeight;

        // Limit log entries (keep last 50)
        const entries = this.voiceLog.querySelectorAll('.voice-entry');
        if (entries.length > 50) {
            entries[0].remove();
        }
    }

    getCurrentTime() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        return `${hours}:${minutes}:${seconds}`;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.geminiVoice = new GeminiVoiceChat();
    });
} else {
    window.geminiVoice = new GeminiVoiceChat();
}
