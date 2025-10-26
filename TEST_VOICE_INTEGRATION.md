# Testing Voice Chat Integration

## Pre-Flight Checklist

### 1. Verify Files Exist

```bash
# Check all required files
ls -la dashboard/dashboard.py
ls -la dashboard/templates/index.html
ls -la dashboard/static/js/audio-streamer.js
ls -la dashboard/static/js/components/gemini-voice.js
ls -la dashboard/static/css/main.css
```

Expected: All files should exist

### 2. Check Dependencies

```bash
# In virtual environment
python -c "import flask_sock; print('✅ flask-sock OK')"
python -c "import websockets; print('✅ websockets OK')"
python -c "import certifi; print('✅ certifi OK')"
python -c "from flask_cors import CORS; print('✅ flask-cors OK')"
```

### 3. Verify Environment Variables

```bash
# Check if .env exists
ls -la .env

# Check if GEMINI_API_KEY is set
grep "GEMINI_API_KEY" .env
```

Expected: Should see your API key (not "your_gemini_api_key_here")

### 4. Check Dashboard HTML

```bash
# Verify voice panel is in HTML
grep -c "Voice Assistant" dashboard/templates/index.html
grep -c "startVoiceBtn" dashboard/templates/index.html
```

Expected: Both should return 1

### 5. Check CSS

```bash
# Verify voice panel is visible (not display:none)
grep "voice-log-panel" dashboard/static/css/main.css | grep -v "display: none"
```

Expected: Should show `.voice-log-panel { grid-column: 9 / 13; grid-row: 4; }`

## Running the Dashboard

### Start Server

```bash
cd dashboard
python dashboard.py
```

Expected output:
```
============================================================
Helios AI Dashboard Starting...
============================================================
Mock Data Mode: True/False
Dashboard URL: http://localhost:5000
Gemini Voice Chat: Enabled
============================================================
```

### Check for Errors

If you see errors:

**"No module named 'flask_sock'"**
```bash
pip install flask-sock simple-websocket
```

**"GEMINI_API_KEY not configured"**
```bash
# Edit .env file and add:
GEMINI_API_KEY=your_actual_api_key_here
```

## Testing in Browser

### 1. Open Dashboard

Navigate to: http://localhost:5000

### 2. Visual Check

You should see **6 panels**:

1. **Top Left**: Live Cloud Coverage Map
2. **Top Right**: Real-Time Analytics
3. **Center Large**: Digital Twin Performance (graph)
4. **Bottom Left (column 9-13, row 2)**: Environmental Impact
5. **Bottom Middle (column 9-13, row 3)**: Safety Monitor
6. **Bottom Right (column 9-13, row 4)**: Voice Assistant ← **NEW!**

### 3. Voice Assistant Panel Contents

The Voice Assistant panel should have:
- **Title**: "Voice Assistant"
- **Two Buttons**:
  - "Start Voice Chat" (gradient button, enabled)
  - "Stop Chat" (red button, disabled)
- **Status Indicator**: Gray dot with "Ready" text
- **Voice Log**: Shows initial message

### 4. Test Voice Chat

1. **Click "Start Voice Chat"**
   - Browser asks for microphone permission → Click "Allow"
   - Status changes to "Connecting..." (yellow dot)
   - Status changes to "Connected" (green pulsing dot)
   - "Stop Chat" button becomes enabled
   - Voice log shows: "Connected! You can start talking."

2. **Speak into microphone**
   - Status dot turns cyan and pulses
   - Voice log shows: "Listening..."

3. **Wait for Gemini response**
   - You should hear Gemini speaking
   - Voice log shows: "Turn complete"

4. **Click "Stop Chat"**
   - Status returns to "Disconnected" (gray)
   - "Start Voice Chat" button becomes enabled again

### 5. Keyboard Test

Press `Ctrl + Space`:
- Should toggle voice chat on/off
- Same behavior as clicking buttons

## Debugging

### Browser Console

Open DevTools (F12) → Console tab

Look for:
```
[AudioStreamer] AudioContext created at 48000Hz
[AudioStreamer] Microphone access granted
[AudioStreamer] WebSocket connected
[Gemini Voice] Component initialized
```

### Network Tab

Open DevTools → Network tab → WS (WebSockets)

You should see:
- Connection to `ws://localhost:5000/ws/gemini-voice`
- Status: 101 Switching Protocols
- Binary frames being sent/received

### Server Terminal

Watch for:
```
[Gemini Voice] Client connected from 127.0.0.1
[Gemini] WebSocket connected
[Gemini] Setup message sent
[Gemini] Setup complete
[Gemini] Initial prompt sent
[Worker] Client->Gemini thread started
[Worker] Gemini->Client thread started
```

## Common Issues

### Panel Not Visible

**Problem**: Voice Assistant panel doesn't appear

**Check**:
```bash
# 1. Verify HTML has the panel
grep -A 5 "Voice Assistant" dashboard/templates/index.html

# 2. Check CSS doesn't hide it
grep "voice-log-panel.*display.*none" dashboard/static/css/main.css
```

**Fix**: If CSS has `display: none`, remove it.

### Grid Layout Issues

**Problem**: Panels overlap or are misaligned

**Check**:
```bash
grep "voice-log-panel.*grid" dashboard/static/css/main.css
```

**Expected**: `.voice-log-panel { grid-column: 9 / 13; grid-row: 4; }`

**Fix**: Ensure voice-log-panel is on row 4, not overlapping with safety-panel (row 3)

### JavaScript Not Loading

**Problem**: Buttons don't work

**Check browser console**: Look for 404 errors on JS files

**Verify**:
```bash
ls -la dashboard/static/js/audio-streamer.js
ls -la dashboard/static/js/components/gemini-voice.js
```

### WebSocket Connection Failed

**Problem**: "Failed to connect to Gemini"

**Check**:
1. GEMINI_API_KEY is valid
2. Internet connection works
3. No firewall blocking WebSocket

**Terminal shows**:
```
[Gemini] Connection error: ...
```

### No Audio Output

**Problem**: Can't hear Gemini speaking

**Check**:
1. Browser audio not muted
2. System volume up
3. Correct audio output device selected
4. Browser console for playback errors

### Microphone Not Working

**Problem**: Status never shows "Speaking"

**Check**:
1. Microphone permission granted
2. Correct input device selected
3. Microphone not muted in system settings
4. Browser console: `[AudioStreamer] Microphone access granted`

## Success Criteria

✅ Dashboard loads at http://localhost:5000
✅ All 6 panels visible (including Voice Assistant)
✅ "Start Voice Chat" button works
✅ Microphone permission granted
✅ Status shows "Connected" with green dot
✅ Can hear Gemini speaking
✅ Voice log updates with activity
✅ "Stop Chat" ends session cleanly

## Performance Check

### Expected Behavior

- **Dashboard load**: < 2 seconds
- **Voice connection**: 2-3 seconds
- **Audio latency**: < 500ms
- **No lag** on other dashboard panels while voice chat active

### If Slow

Check terminal for errors:
- Thread deadlocks
- WebSocket timeouts
- Memory issues

## Next Steps

Once everything works:

1. ✅ Customize AI personality in `dashboard.py`
2. ✅ Change voice (Puck → Charon/Kore/Fenrir/Aoede)
3. ✅ Adjust button colors in CSS
4. ✅ Test with real solar data (if available)
5. ✅ Deploy to production (set DEBUG_MODE=False)

---

**Having issues?** Check [VOICE_INTEGRATION.md](VOICE_INTEGRATION.md) for detailed troubleshooting.
