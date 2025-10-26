/**
 * Gemini Voice Chat - Integrated with Voice Visualizer
 * Connects the visualizer UI to Gemini Live API
 */

class GeminiVoiceIntegrated {
    constructor() {
        this.ws = null;
        this.audioContext = null;
        this.mediaStream = null;
        this.processor = null;
        this.nextPlayTime = 0;
        this.isConnected = false;

        // Audio configuration
        this.GEMINI_INPUT_RATE = 16000;
        this.GEMINI_OUTPUT_RATE = 24000;
        this.nativeSampleRate = 48000;

        // WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.wsUrl = `${protocol}//${window.location.host}/ws/gemini-voice`;

        // UI Elements
        this.statusText = document.getElementById('voiceStatus');
        this.overlay = document.getElementById('voiceVisualizerOverlay');
        this.toggleBtn = document.getElementById('toggleVoiceVisualizer');
        this.closeBtn = document.getElementById('closeVoiceVisualizer');

        // Voice visualizer instance (will be set externally)
        this.visualizer = null;

        console.log('[GeminiVoice] Initialized');
    }

    setVisualizer(visualizer) {
        this.visualizer = visualizer;
    }

    async start(mediaStream, audioContext) {
        if (this.isConnected) {
            console.log('[GeminiVoice] Already connected');
            return;
        }

        this.mediaStream = mediaStream;
        this.audioContext = audioContext;
        this.nativeSampleRate = audioContext.sampleRate;

        try {
            this.updateStatus('Connecting to Helios AI...');

            // Connect to WebSocket
            await this.connectWebSocket();

            // Start audio processing
            this.startAudioProcessing();

            this.isConnected = true;
            this.updateStatus('Connected - Start talking!');

            console.log('[GeminiVoice] Started successfully');

        } catch (error) {
            console.error('[GeminiVoice] Start error:', error);
            this.updateStatus(`Error: ${error.message}`);
            this.stop();
        }
    }

    connectWebSocket() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.wsUrl);
                this.ws.binaryType = 'arraybuffer';

                this.ws.onopen = () => {
                    console.log('[GeminiVoice] WebSocket connected');
                };

                this.ws.onmessage = (event) => {
                    if (typeof event.data === 'string') {
                        const message = JSON.parse(event.data);
                        console.log('[GeminiVoice] Received:', message);

                        if (message.status === 'ready') {
                            resolve();
                        } else if (message.error) {
                            reject(new Error(message.error));
                        }
                    } else {
                        // Binary audio from Gemini
                        this.playAudioChunk(event.data);
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('[GeminiVoice] WebSocket error:', error);
                    reject(new Error('WebSocket connection failed'));
                };

                this.ws.onclose = () => {
                    console.log('[GeminiVoice] WebSocket closed');
                    this.updateStatus('Disconnected');
                };

            } catch (error) {
                reject(error);
            }
        });
    }

    startAudioProcessing() {
        const source = this.audioContext.createMediaStreamSource(this.mediaStream);

        const bufferSize = 4096;
        this.processor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);

        this.processor.onaudioprocess = (event) => {
            if (!this.isConnected) return;

            const inputBuffer = event.inputBuffer;
            const inputData = inputBuffer.getChannelData(0);

            // Resample to 16kHz
            const resampled = this.resample(
                inputData,
                this.nativeSampleRate,
                this.GEMINI_INPUT_RATE
            );

            // Convert to Int16 PCM
            const pcmData = this.floatTo16BitPCM(resampled);

            // Send to WebSocket
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(pcmData.buffer);
            }
        };

        source.connect(this.processor);
        this.processor.connect(this.audioContext.destination);

        console.log('[GeminiVoice] Audio processing started');
    }

    resample(inputBuffer, inputRate, outputRate) {
        if (inputRate === outputRate) {
            return inputBuffer;
        }

        const ratio = inputRate / outputRate;
        const outputLength = Math.round(inputBuffer.length / ratio);
        const output = new Float32Array(outputLength);

        for (let i = 0; i < outputLength; i++) {
            const position = i * ratio;
            const index = Math.floor(position);
            const fraction = position - index;

            if (index + 1 < inputBuffer.length) {
                output[i] = inputBuffer[index] * (1 - fraction) +
                           inputBuffer[index + 1] * fraction;
            } else {
                output[i] = inputBuffer[index];
            }
        }

        return output;
    }

    floatTo16BitPCM(float32Array) {
        const int16Array = new Int16Array(float32Array.length);

        for (let i = 0; i < float32Array.length; i++) {
            const clamped = Math.max(-1, Math.min(1, float32Array[i]));
            int16Array[i] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7FFF;
        }

        return int16Array;
    }

    int16ToFloat32(arrayBuffer) {
        const int16Array = new Int16Array(arrayBuffer);
        const float32Array = new Float32Array(int16Array.length);

        for (let i = 0; i < int16Array.length; i++) {
            float32Array[i] = int16Array[i] / (int16Array[i] < 0 ? 0x8000 : 0x7FFF);
        }

        return float32Array;
    }

    playAudioChunk(arrayBuffer) {
        try {
            const float32Data = this.int16ToFloat32(arrayBuffer);

            const audioBuffer = this.audioContext.createBuffer(
                1,
                float32Data.length,
                this.GEMINI_OUTPUT_RATE
            );

            audioBuffer.getChannelData(0).set(float32Data);

            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);

            const currentTime = this.audioContext.currentTime;
            const duration = audioBuffer.duration;

            if (this.nextPlayTime < currentTime) {
                this.nextPlayTime = currentTime;
            }

            source.start(this.nextPlayTime);
            this.nextPlayTime += duration;

        } catch (error) {
            console.error('[GeminiVoice] Playback error:', error);
        }
    }

    stop() {
        console.log('[GeminiVoice] Stopping...');

        // Stop audio processing
        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }

        // Close WebSocket
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.isConnected = false;
        this.nextPlayTime = 0;
        this.updateStatus('Ready to listen...');

        console.log('[GeminiVoice] Stopped');
    }

    updateStatus(message) {
        if (this.statusText) {
            this.statusText.textContent = message;
        }
        console.log(`[GeminiVoice] Status: ${message}`);
    }
}

// Export
window.GeminiVoiceIntegrated = GeminiVoiceIntegrated;
console.log('[GeminiVoice] Integration loaded');
