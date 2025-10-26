/**
 * Gemini Voice Integration for Helios Dashboard
 * Uses Google's Multimodal Live API directly in the browser
 */

class GeminiVoice {
    constructor() {
        this.apiKey = null;
        this.isListening = false;
        this.audioContext = null;
        this.analyser = null;
        this.microphone = null;
        this.mediaRecorder = null;
        this.audioChunks = [];

        // // Wake word detection state
        // this.wakeWordDetected = false;
        // this.recordingQuestion = false;
        // this.questionChunks = [];
        // this.questionStartTime = null;

        // UI elements
        this.micButton = null;
        this.statusText = null;

        // Socket for system data
        this.socket = window.socket;

        this.init();
    }

    async init() {
        // Get API key from dashboard config
        try {
            const response = await fetch('/api/gemini-config');
            const config = await response.json();
            this.apiKey = config.api_key;

            if (!this.apiKey) {
                console.error('No Gemini API key configured');
                this.showError('API key not configured');
                return;
            }

            this.setupUI();
        } catch (error) {
            console.error('Failed to load Gemini config:', error);
            this.showError('Configuration error');
        }
    }

    setupUI() {
        // Add microphone button to the AI voice panel
        const voicePanel = document.querySelector('.ai-voice-panel');
        if (!voicePanel) return;

        const statusIndicator = document.querySelector('.status-indicator');
        this.statusText = document.querySelector('.status-text');

        // Add mic button
        const micButton = document.createElement('button');
        micButton.className = 'mic-button';
        micButton.innerHTML = '🎤';
        micButton.title = 'Click to start listening';
        micButton.addEventListener('click', () => this.toggleListening());

        const wakeWordStatus = document.getElementById('wakeWordStatus');
        wakeWordStatus.appendChild(micButton);

        this.micButton = micButton;
    }

    async toggleListening() {
        if (this.isListening) {
            this.stopListening();
        } else {
            await this.startListening();
        }
    }

    async startListening() {
        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // Setup audio context for visualization
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;

            this.microphone = this.audioContext.createMediaStreamSource(stream);
            this.microphone.connect(this.analyser);

            // Setup media recorder for sending to backend
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = async (event) => {
                if (event.data.size > 0) {
                    if (!this.recordingQuestion) {
                        // Phase 1: Looking for wake word "Helios"
                        this.audioChunks.push(event.data);
                        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                        const wakeWordFound = await this.checkForWakeWord(audioBlob);

                        if (wakeWordFound) {
                            console.log('🎯 Wake word detected! Now listening for your question...');
                            this.wakeWordDetected = true;
                            this.recordingQuestion = true;
                            this.questionStartTime = Date.now();
                            this.questionChunks = [];
                            this.updateStatus('Listening for your question...');

                            // Activate wake word UI
                            if (window.aiVoiceInterface) {
                                window.aiVoiceInterface.activateWakeWord('Helios detected');
                            }
                        }

                        // Clear chunks to prevent memory buildup
                        this.audioChunks = [];
                    } else {
                        // Phase 2: Recording the question after "Helios"
                        this.questionChunks.push(event.data);

                        // After 5 seconds of recording the question, process it
                        const questionDuration = Date.now() - this.questionStartTime;
                        if (questionDuration >= 5000) {
                            const questionBlob = new Blob(this.questionChunks, { type: 'audio/wav' });
                            await this.processQuestion(questionBlob);

                            // Reset state for next wake word
                            this.wakeWordDetected = false;
                            this.recordingQuestion = false;
                            this.questionChunks = [];
                            this.updateStatus('Listening... Say "Helios" to activate');
                        }
                    }
                }
            };

            this.mediaRecorder.onstop = () => {
                // Clean up when stopped
                this.audioChunks = [];
            };

            // Start recording with 2-second chunks
            this.mediaRecorder.start(2000);
            this.isListening = true;

            // Update UI
            this.micButton.classList.add('listening');
            this.micButton.innerHTML = '⏹️';
            this.micButton.title = 'Click to stop';
            this.updateStatus('Listening... Say "Helios" to activate');

            // Start visualizing
            if (window.aiVoiceInterface) {
                window.aiVoiceInterface.startRealAudio(this.analyser);
            }

            console.log('✅ Microphone active');

        } catch (error) {
            console.error('Microphone access error:', error);
            this.showError('Microphone access denied');
        }
    }

    stopListening() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }

        if (this.microphone) {
            this.microphone.disconnect();
            this.microphone.mediaStream.getTracks().forEach(track => track.stop());
        }

        if (this.audioContext) {
            this.audioContext.close();
        }

        this.isListening = false;

        // Update UI
        this.micButton.classList.remove('listening');
        this.micButton.innerHTML = '🎤';
        this.micButton.title = 'Click to start listening';
        this.updateStatus('Click mic to start');

        console.log('⏹️ Microphone stopped');
    }

    async checkForWakeWord(audioBlob) {
        try {
            // Convert to base64
            const base64Audio = await this.blobToBase64(audioBlob);

            // Send to backend to check for wake word only
            const response = await fetch('/api/check-wake-word', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    audio: base64Audio
                })
            });

            const result = await response.json();
            return result.wake_word_detected || false;
        } catch (error) {
            console.error('Wake word detection error:', error);
            return false;
        }
    }

    async processQuestion(audioBlob) {
        try {
            this.updateStatus('Processing your question...');

            // Convert to base64
            const base64Audio = await this.blobToBase64(audioBlob);

            // Send to backend for Gemini processing with full question
            const response = await fetch('/api/voice-query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    audio: base64Audio,
                    system_data: this.getSystemData(),
                    wake_word_confirmed: true  // We already detected it
                })
            });

            const result = await response.json();

            if (result.response_text) {
                this.handleResponse(result.response_text);

                // Speak the response
                if (result.response_audio) {
                    this.speakResponse(result.response_audio);
                } else {
                    // Fallback to Web Speech API
                    this.speak(result.response_text);
                }
            }
        } catch (error) {
            console.error('Question processing error:', error);
            this.showError('Processing error');
        }
    }

    blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result.split(',')[1]);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    handleWakeWordDetected() {
        console.log('🎯 Wake word "Helios" detected!');

        // Activate UI
        if (window.aiVoiceInterface) {
            window.aiVoiceInterface.activateWakeWord('Helios detected');
        }

        this.updateStatus('Processing your question...');
    }

    handleResponse(text) {
        console.log('💬 Response:', text);

        // Update UI
        if (window.aiVoiceInterface) {
            window.aiVoiceInterface.updateResponse(text);
        }

        this.updateStatus('Listening... Say "Helios" to activate');
    }

    speak(text) {
        // Fallback: Use Web Speech API for TTS
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.85;  // Slightly slower for clarity
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        window.speechSynthesis.speak(utterance);
    }

    speakResponse(base64Audio) {
        // Play audio response from Gemini
        const audio = new Audio('data:audio/wav;base64,' + base64Audio);
        audio.play();
    }

    getSystemData() {
        // Get latest system data for context
        return {
            sensors: window.latestSensorData || {},
            status: window.latestStatusData || {},
            impact: window.latestImpactData || {},
            safety: window.latestSafetyData || {}
        };
    }

    updateStatus(message) {
        if (this.statusText) {
            this.statusText.textContent = message;
        }
    }

    showError(message) {
        console.error('❌', message);
        this.updateStatus(`Error: ${message}`);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.geminiVoice = new GeminiVoice();
});
