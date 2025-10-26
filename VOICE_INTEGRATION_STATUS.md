# Helios AI Voice Integration - Current Status

## Overview

I understand now - you want the Gemini voice model (`gemini-2.5-flash-native-audio-dialog`) to run **embedded in the dashboard**, not as a separate service. This is a much cleaner architecture!

## What We've Built So Far

### ✅ Completed:
1. **Model Updated** - Changed to `gemini-2.5-flash-native-audio-dialog` in [adk/helios_agent/agent.py](adk/helios_agent/agent.py)
2. **Dashboard Layout** - AI Voice panel is now horizontal and positioned below the Digital Twin Performance graph
3. **Voice Handler Backend** - Created [dashboard/voice_handler.py](dashboard/voice_handler.py) with Gemini integration
4. **WebSocket Endpoint** - Added `voice_input` handler in [dashboard/dashboard.py](dashboard/dashboard.py)

### 🔄 What's Needed Next:

The main challenge is that `gemini-2.5-flash-native-audio-dialog` is designed for **bidirectional real-time audio streaming**, which requires:

1. **Continuous audio input** from browser microphone
2. **Server-side handling** of audio streams
3. **Real-time audio output** back to the browser

This is more complex than the simple WebSocket approach we started with.

## Two Possible Approaches:

### Option 1: Use Gemini SDK Directly (What You Want)
**Architecture:**
```
Browser Mic → WebSocket → Dashboard (Python) → Gemini API → Response → Browser Speakers
```

**Pros:**
- All in one service (dashboard only)
- No port 8001 needed
- Cleaner architecture

**Cons:**
- Requires complex audio streaming setup
- Need to handle Web Audio API + WebSocket binary streams
- Gemini SDK may not work well with this approach

### Option 2: Keep ADK Web Service (Current Setup)
**Architecture:**
```
Dashboard (Port 5000) - Visual interface with spectrogram
ADK Agent (Port 8001) - Gemini voice processing
```

**Pros:**
- ADK handles all the complex audio streaming
- Already working
- Easy to use (just click mic button)

**Cons:**
- Two services to run
- Uses port 8001

## Recommended Solution:

Since you want **everything in the dashboard**, here's what I recommend:

### Use Google's Web-based Multimodal Live API

Instead of the Python SDK, we can use the **JavaScript/browser-based Gemini Multimodal Live API** which is specifically designed for this use case:

```javascript
// In the browser (dashboard frontend)
const session = await genai.live.connect({
  model: "gemini-2.5-flash-native-audio-dialog"
});

// Send audio from microphone
session.sendAudio(audioData);

// Receive responses
session.on('response', (response) => {
  // Play audio response
  // Update UI
});
```

This would allow:
- ✅ Everything runs through the dashboard
- ✅ No ADK web service needed
- ✅ Real-time audio I/O in the browser
- ✅ Wake word detection via Gemini
- ✅ Single service (dashboard only)

## Next Steps - Your Choice:

### A) Implement Browser-based Gemini (My Recommendation)
I can create a JavaScript module that:
- Connects to Gemini Multimodal Live API directly from the browser
- Handles microphone input
- Processes wake word detection
- Plays audio responses
- Updates the spectrogram visualization

This would be a **pure dashboard solution** with no ADK web service.

### B) Simplify Current Setup
Keep the two-service model but make it easier:
- Single command to start both services
- Dashboard shows status of both services
- Clearer documentation

### C) Hybrid Approach
- Dashboard handles UI and data visualization
- Small Python backend service (part of dashboard) handles Gemini API calls
- No separate ADK service

## What Would You Like Me To Do?

Please let me know which approach you prefer:
1. **Full browser integration** (Option A) - Everything in dashboard, no separate services
2. **Keep current setup** (Option B) - Two services, but simplified
3. **Hybrid** (Option C) - Dashboard + small backend helper

I'm ready to implement whichever you choose!
