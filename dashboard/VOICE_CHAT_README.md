# Helios Voice Chat - Gemini Live API Integration

Real-time audio-to-audio conversational AI using Google Gemini's Live API with Flask backend.

## Features

- **Real-time Voice Conversation**: Bidirectional audio streaming with Gemini 2.5 Flash
- **Two Implementation Approaches**: Threading-based (recommended) and asyncio-based
- **Production-Ready**: SSL verification, error handling, connection cleanup
- **Audio Processing**:
  - Client-side resampling (browser native → 16kHz for Gemini)
  - Server-side base64 encoding/decoding
  - Sequential audio playback queue (prevents choppy audio)
- **Visual Feedback**: Connection status, speaking indicator, error messages
- **Browser Optimized**: Echo cancellation, noise suppression, auto-gain control

## Architecture

```
Browser (48kHz) → Resample to 16kHz → WebSocket → Flask Server
                                                      ↓
                                              Gemini Live API
                                                      ↓
Browser ← 24kHz Audio ← Base64 Decode ← WebSocket ← Server
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `flask==3.0.0`
- `flask-sock==0.7.0`
- `simple-websocket==1.0.0`
- `websockets==12.0`
- `certifi==2024.2.2`
- `flask-cors==4.0.0`
- `python-dotenv==1.0.0`

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_random_secret_key
ALLOWED_ORIGINS=http://localhost:5001,http://127.0.0.1:5001
```

Get your Gemini API key: https://aistudio.google.com/app/apikey

### 3. Run the Application

```bash
cd dashboard
python voice_chat.py
```

The server will start on `http://localhost:5001`

### 4. Access the Voice Chat

Open your browser and navigate to:
```
http://localhost:5001/voice
```

## Usage

1. **Click "Start Chat"** - Grants microphone permission and connects to Gemini
2. **Start Talking** - Gemini will introduce itself and begin conversation
3. **Click "Stop Chat"** - Ends the session and disconnects

### Keyboard Shortcuts

- `Space` - Toggle chat on/off
- `Escape` - Stop chat

## File Structure

```
dashboard/
├── voice_chat.py                    # Flask backend with WebSocket
├── templates/
│   └── voice_chat.html             # Frontend UI
├── static/
│   └── js/
│       └── audio-streamer.js       # Audio streaming client
└── VOICE_CHAT_README.md            # This file
```

## Implementation Details

### Backend (voice_chat.py)

**Threading Approach (Recommended)**:
- Uses `flask-sock` for WebSocket support
- Two worker threads for bidirectional streaming:
  - `client_to_gemini_worker()`: Forwards audio from client to Gemini
  - `gemini_to_client_worker()`: Forwards audio from Gemini to client
- Thread-safe queues for message passing
- SSL context with `certifi` for production security

**Key Components**:
```python
# SSL Context (CRITICAL!)
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Audio MIME type (MUST specify rate!)
"mime_type": "audio/pcm;rate=16000"

# System instruction (customize AI personality)
SYSTEM_INSTRUCTION = {
    "parts": [{"text": "You are Helios..."}]
}
```

### Frontend (audio-streamer.js)

**Audio Pipeline**:
1. Capture microphone at native rate (typically 48kHz)
2. Resample to 16kHz using linear interpolation
3. Convert Float32 to Int16 PCM
4. Send binary data via WebSocket
5. Receive 24kHz PCM from server
6. Convert Int16 to Float32
7. Create AudioBuffer at 24kHz
8. Queue for sequential playback

**Critical Details**:
```javascript
// Resampling (native → 16kHz)
const resampled = this.resample(inputData, nativeSampleRate, 16000);

// Audio playback at 24kHz (MUST match Gemini output!)
const audioBuffer = audioContext.createBuffer(1, samples, 24000);

// Sequential playback (prevents overlapping audio)
source.start(this.nextPlayTime);
this.nextPlayTime += duration;
```

## Customization

### Change AI Personality

Edit `SYSTEM_INSTRUCTION` in [voice_chat.py](voice_chat.py:31-40):

```python
SYSTEM_INSTRUCTION = {
    "parts": [{
        "text": """You are a helpful assistant...

        IMPORTANT: Ask ONE question at a time and WAIT for responses."""
    }]
}
```

### Change Voice

Edit `voice_name` in [voice_chat.py](voice_chat.py:70-75):

```python
"prebuilt_voice_config": {
    "voice_name": "Puck"  # Options: Puck, Charon, Kore, Fenrir, Aoede
}
```

### Adjust Audio Settings

**Input Sample Rate** (change from 16kHz):
- Update `GEMINI_INPUT_RATE` in audio-streamer.js
- Update `mime_type` in voice_chat.py

**Speaking Detection Threshold**:
```javascript
// In audio-streamer.js
const SPEAKING_THRESHOLD = 0.01;  // Adjust sensitivity
```

## Troubleshooting

### "Failed to connect to Gemini"
- Check your `GEMINI_API_KEY` in `.env`
- Verify internet connection
- Check firewall settings

### Audio is Garbled/Fast/Slow
- **Cause**: Incorrect sample rate specification
- **Fix**: Ensure `mime_type: "audio/pcm;rate=16000"` in backend
- **Fix**: Ensure `createBuffer(..., 24000)` in frontend

### Audio is Choppy/Overlapping
- **Cause**: Concurrent audio playback
- **Fix**: Sequential playback queue is implemented correctly

### Microphone Permission Denied
- Browser requires HTTPS for getUserMedia (except localhost)
- Allow microphone access in browser settings

### WebSocket Connection Failed
- Check `ALLOWED_ORIGINS` in `.env` matches your URL
- Verify Flask server is running on correct port

## API Endpoints

### HTTP Routes

- `GET /voice` - Voice chat UI
- `GET /health` - Health check

### WebSocket Routes

- `ws://localhost:5001/ws/voice-chat` - Voice chat WebSocket

## Technical Notes

### Sample Rate Handling

**Critical**: Gemini requires explicit sample rate specification!

```
Input:  Browser (48kHz) → Resample → 16kHz → Gemini
Output: Gemini → 24kHz → Browser playback
```

Wrong rate = unintelligible audio!

### SSL Verification

**Production**: Always use `certifi` for SSL context:
```python
ssl_context = ssl.create_default_context(cafile=certifi.where())
```

**Development**: SSL verification is still enabled (recommended)

### Sequential Playback

Prevents audio overlap by queueing buffers:
```javascript
const currentTime = audioContext.currentTime;
if (nextPlayTime < currentTime) {
    nextPlayTime = currentTime;
}
source.start(nextPlayTime);
nextPlayTime += duration;
```

## Alternative Implementation: Asyncio

See [voice_chat.py](voice_chat.py:250-350) for asyncio-based implementation:

```python
async def handle_voice_chat_async(client_ws):
    async with websockets.connect(GEMINI_WS_URL, ssl=ssl_context) as gemini_ws:
        await asyncio.gather(
            client_to_gemini(),
            gemini_to_client()
        )
```

**Note**: Requires async-compatible WebSocket library (not flask-sock)

## Resources

- [Gemini Live API Docs](https://ai.google.dev/api/multimodal-live)
- [Get API Key](https://aistudio.google.com/app/apikey)
- [Flask-Sock Documentation](https://flask-sock.readthedocs.io/)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)

## License

Part of the Helios AI project.

## Credits

Built with:
- Google Gemini 2.5 Flash (Native Audio Thinking Dialog)
- Flask & Flask-Sock
- Web Audio API
- WebSockets

---

**Need Help?** Check the troubleshooting section or review the inline code comments in [voice_chat.py](voice_chat.py) and [audio-streamer.js](../static/js/audio-streamer.js).
