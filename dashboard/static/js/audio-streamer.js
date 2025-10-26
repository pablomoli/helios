/**
 * Audio Streamer for Gemini Live API Voice Chat
 * Handles microphone capture, audio resampling, and WebSocket streaming
 */

class AudioStreamer {
    constructor(wsUrl) {
        this.wsUrl = wsUrl;
        this.ws = null;
        this.audioContext = null;
        this.mediaStream = null;
        this.processor = null;
        this.nextPlayTime = 0;
        this.isConnected = false;
        this.isSpeaking = false;

        // Audio configuration
        this.GEMINI_INPUT_RATE = 16000;   // Gemini expects 16kHz input
        this.GEMINI_OUTPUT_RATE = 24000;  // Gemini outputs 24kHz
        this.nativeSampleRate = 48000;    // Browser default (will be detected)

        // Callbacks
        this.onStatusChange = null;
        this.onSpeakingChange = null;
        this.onError = null;
    }

    /**
     * Connect to the voice chat server and start streaming
     */
    async connect() {
        try {
            this.setStatus('connecting');

            // Create AudioContext at browser's native sample rate
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.nativeSampleRate = this.audioContext.sampleRate;
            console.log(`[AudioStreamer] AudioContext created at ${this.nativeSampleRate}Hz`);

            // Request microphone access with audio constraints
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: this.nativeSampleRate
                }
            });
            console.log('[AudioStreamer] Microphone access granted');

            // Create WebSocket connection
            await this.connectWebSocket();

            // Start audio processing
            this.startAudioProcessing();

            this.isConnected = true;
            this.setStatus('connected');

        } catch (error) {
            console.error('[AudioStreamer] Connection error:', error);
            this.handleError(error.message || 'Failed to connect');
            this.disconnect();
        }
    }

    /**
     * Connect to WebSocket server
     */
    connectWebSocket() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.wsUrl);
                this.ws.binaryType = 'arraybuffer';

                this.ws.onopen = () => {
                    console.log('[AudioStreamer] WebSocket connected');
                };

                this.ws.onmessage = (event) => {
                    if (typeof event.data === 'string') {
                        // JSON message (status updates)
                        const message = JSON.parse(event.data);
                        console.log('[AudioStreamer] Received:', message);

                        if (message.status === 'ready') {
                            resolve();
                        } else if (message.error) {
                            reject(new Error(message.error));
                        }
                    } else {
                        // Binary audio data from Gemini (24kHz PCM)
                        this.playAudioChunk(event.data);
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('[AudioStreamer] WebSocket error:', error);
                    reject(new Error('WebSocket connection failed'));
                };

                this.ws.onclose = () => {
                    console.log('[AudioStreamer] WebSocket closed');
                    this.setStatus('disconnected');
                };

            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Start audio processing pipeline
     */
    startAudioProcessing() {
        // Create audio source from microphone
        const source = this.audioContext.createMediaStreamSource(this.mediaStream);

        // Create ScriptProcessorNode for audio processing
        // Buffer size: 4096 samples (good balance between latency and performance)
        const bufferSize = 4096;
        this.processor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);

        this.processor.onaudioprocess = (event) => {
            const inputBuffer = event.inputBuffer;
            const inputData = inputBuffer.getChannelData(0); // Float32Array at native rate

            // Detect speaking (volume level)
            this.detectSpeaking(inputData);

            // Resample from native rate to 16kHz for Gemini
            const resampled = this.resample(
                inputData,
                this.nativeSampleRate,
                this.GEMINI_INPUT_RATE
            );

            // Convert Float32 to Int16 PCM
            const pcmData = this.floatTo16BitPCM(resampled);

            // Send to WebSocket
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(pcmData.buffer);
            }
        };

        // Connect the audio graph
        source.connect(this.processor);
        this.processor.connect(this.audioContext.destination);

        console.log('[AudioStreamer] Audio processing started');
    }

    /**
     * Resample audio using linear interpolation
     * @param {Float32Array} inputBuffer - Input audio at source sample rate
     * @param {number} inputRate - Source sample rate
     * @param {number} outputRate - Target sample rate
     * @returns {Float32Array} - Resampled audio
     */
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
                // Linear interpolation
                output[i] = inputBuffer[index] * (1 - fraction) +
                           inputBuffer[index + 1] * fraction;
            } else {
                output[i] = inputBuffer[index];
            }
        }

        return output;
    }

    /**
     * Convert Float32 audio to Int16 PCM
     * @param {Float32Array} float32Array - Input audio (-1.0 to 1.0)
     * @returns {Int16Array} - PCM audio data
     */
    floatTo16BitPCM(float32Array) {
        const int16Array = new Int16Array(float32Array.length);

        for (let i = 0; i < float32Array.length; i++) {
            // Clamp to [-1, 1] range
            const clamped = Math.max(-1, Math.min(1, float32Array[i]));
            // Convert to 16-bit PCM
            int16Array[i] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7FFF;
        }

        return int16Array;
    }

    /**
     * Convert Int16 PCM to Float32 audio
     * @param {ArrayBuffer} arrayBuffer - Binary PCM data
     * @returns {Float32Array} - Audio data (-1.0 to 1.0)
     */
    int16ToFloat32(arrayBuffer) {
        const int16Array = new Int16Array(arrayBuffer);
        const float32Array = new Float32Array(int16Array.length);

        for (let i = 0; i < int16Array.length; i++) {
            // Convert from 16-bit PCM to float (-1.0 to 1.0)
            float32Array[i] = int16Array[i] / (int16Array[i] < 0 ? 0x8000 : 0x7FFF);
        }

        return float32Array;
    }

    /**
     * Play audio chunk from Gemini (24kHz PCM)
     * Uses sequential playback queue to prevent overlapping audio
     * @param {ArrayBuffer} arrayBuffer - Binary PCM data at 24kHz
     */
    playAudioChunk(arrayBuffer) {
        try {
            // Convert Int16 PCM to Float32
            const float32Data = this.int16ToFloat32(arrayBuffer);

            // Create AudioBuffer at 24kHz (CRITICAL: must match Gemini's output rate!)
            const audioBuffer = this.audioContext.createBuffer(
                1,  // mono
                float32Data.length,
                this.GEMINI_OUTPUT_RATE  // 24kHz
            );

            // Copy data to buffer
            audioBuffer.getChannelData(0).set(float32Data);

            // Create buffer source
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);

            // Calculate when to play (sequential queue)
            const currentTime = this.audioContext.currentTime;
            const duration = audioBuffer.duration;

            // If nextPlayTime is in the past, start immediately
            if (this.nextPlayTime < currentTime) {
                this.nextPlayTime = currentTime;
            }

            // Schedule playback
            source.start(this.nextPlayTime);

            // Update next play time (with small gap to prevent clicks)
            this.nextPlayTime += duration;

        } catch (error) {
            console.error('[AudioStreamer] Playback error:', error);
        }
    }

    /**
     * Detect if user is speaking based on volume level
     * @param {Float32Array} audioData - Audio samples
     */
    detectSpeaking(audioData) {
        // Calculate RMS (Root Mean Square) volume
        let sum = 0;
        for (let i = 0; i < audioData.length; i++) {
            sum += audioData[i] * audioData[i];
        }
        const rms = Math.sqrt(sum / audioData.length);

        // Threshold for speaking detection (adjust as needed)
        const SPEAKING_THRESHOLD = 0.01;

        const speaking = rms > SPEAKING_THRESHOLD;

        if (speaking !== this.isSpeaking) {
            this.isSpeaking = speaking;
            if (this.onSpeakingChange) {
                this.onSpeakingChange(speaking);
            }
        }
    }

    /**
     * Disconnect and cleanup
     */
    disconnect() {
        console.log('[AudioStreamer] Disconnecting...');

        // Stop audio processing
        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }

        // Stop microphone
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        // Close WebSocket
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        // Close AudioContext
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        this.isConnected = false;
        this.nextPlayTime = 0;
        this.setStatus('disconnected');

        console.log('[AudioStreamer] Disconnected');
    }

    /**
     * Set connection status and trigger callback
     */
    setStatus(status) {
        console.log(`[AudioStreamer] Status: ${status}`);
        if (this.onStatusChange) {
            this.onStatusChange(status);
        }
    }

    /**
     * Handle error and trigger callback
     */
    handleError(message) {
        console.error(`[AudioStreamer] Error: ${message}`);
        if (this.onError) {
            this.onError(message);
        }
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AudioStreamer;
}
