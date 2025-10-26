#!/bin/bash
#
# Voice Chat Integration Verification Script
# Checks that all components are properly integrated
#

echo "=============================================="
echo "  Helios Voice Chat - Integration Check"
echo "=============================================="
echo ""

ERRORS=0

# Check 1: Voice panel in HTML
echo "✓ Checking HTML..."
if grep -q "Voice Assistant" dashboard/templates/index.html && \
   grep -q "startVoiceBtn" dashboard/templates/index.html; then
    echo "  ✅ Voice Assistant panel found in HTML"
else
    echo "  ❌ Voice Assistant panel NOT found in HTML"
    ERRORS=$((ERRORS + 1))
fi

# Check 2: Voice panel CSS (not hidden)
echo ""
echo "✓ Checking CSS..."
if grep "voice-log-panel" dashboard/static/css/main.css | grep -q "grid-row: 4" && \
   ! grep "voice-log-panel.*display.*none" dashboard/static/css/main.css > /dev/null 2>&1; then
    echo "  ✅ Voice panel CSS configured (row 4, visible)"
else
    echo "  ⚠️  Voice panel CSS may have issues"
    grep "voice-log-panel" dashboard/static/css/main.css | head -1
    ERRORS=$((ERRORS + 1))
fi

# Check 3: JavaScript files exist
echo ""
echo "✓ Checking JavaScript files..."
if [ -f "dashboard/static/js/audio-streamer.js" ]; then
    echo "  ✅ audio-streamer.js exists"
else
    echo "  ❌ audio-streamer.js NOT found"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "dashboard/static/js/components/gemini-voice.js" ]; then
    echo "  ✅ gemini-voice.js exists"
else
    echo "  ❌ gemini-voice.js NOT found"
    ERRORS=$((ERRORS + 1))
fi

# Check 4: Backend integration
echo ""
echo "✓ Checking backend integration..."
if grep -q "from flask_sock import Sock" dashboard/dashboard.py && \
   grep -q "GeminiVoiceConnection" dashboard/dashboard.py && \
   grep -q "/ws/gemini-voice" dashboard/dashboard.py; then
    echo "  ✅ Backend integration found in dashboard.py"
else
    echo "  ❌ Backend integration NOT found"
    ERRORS=$((ERRORS + 1))
fi

# Check 5: Environment file
echo ""
echo "✓ Checking environment configuration..."
if [ -f ".env" ]; then
    if grep -q "GEMINI_API_KEY=" .env && ! grep -q "GEMINI_API_KEY=your_gemini_api_key_here" .env; then
        echo "  ✅ .env file exists with GEMINI_API_KEY"
    else
        echo "  ⚠️  .env exists but GEMINI_API_KEY not configured"
        echo "     Edit .env and add your API key from:"
        echo "     https://aistudio.google.com/app/apikey"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "  ⚠️  .env file not found"
    echo "     Run: cp .env.example .env"
    echo "     Then add your GEMINI_API_KEY"
    ERRORS=$((ERRORS + 1))
fi

# Check 6: Dependencies (if in venv)
echo ""
echo "✓ Checking Python dependencies..."
if python -c "import flask_sock" 2>/dev/null; then
    echo "  ✅ flask-sock installed"
else
    echo "  ❌ flask-sock NOT installed"
    echo "     Run: pip install flask-sock simple-websocket"
    ERRORS=$((ERRORS + 1))
fi

if python -c "import websockets" 2>/dev/null; then
    echo "  ✅ websockets installed"
else
    echo "  ❌ websockets NOT installed"
    echo "     Run: pip install websockets"
    ERRORS=$((ERRORS + 1))
fi

if python -c "import certifi" 2>/dev/null; then
    echo "  ✅ certifi installed"
else
    echo "  ❌ certifi NOT installed"
    echo "     Run: pip install certifi"
    ERRORS=$((ERRORS + 1))
fi

# Summary
echo ""
echo "=============================================="
if [ $ERRORS -eq 0 ]; then
    echo "  ✅ All checks passed!"
    echo ""
    echo "  You're ready to run the dashboard:"
    echo "  cd dashboard && python dashboard.py"
    echo ""
    echo "  Then visit: http://localhost:5000"
else
    echo "  ⚠️  Found $ERRORS issue(s)"
    echo ""
    echo "  Please fix the issues above before running."
    echo ""
    echo "  Quick fixes:"
    echo "  1. Install dependencies: pip install -r requirements.txt"
    echo "  2. Configure API key: cp .env.example .env && nano .env"
    echo "  3. Check file locations match project structure"
fi
echo "=============================================="
