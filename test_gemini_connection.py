#!/usr/bin/env python3
"""
Test Gemini Live API Connection
Helps diagnose voice chat connection issues
"""
import os
import sys
import asyncio
import json
import ssl
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed, reading .env manually")
    # Manual .env parsing
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, _, value = line.partition('=')
                    os.environ[key.strip()] = value.strip()

try:
    import websockets
    import certifi
except ImportError:
    print("❌ Missing dependencies!")
    print("   Run: pip install websockets certifi")
    sys.exit(1)

# Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = "models/gemini-2.5-flash-exp-native-audio-thinking-dialog"

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found in environment")
    print("   Check your .env file")
    sys.exit(1)

if GEMINI_API_KEY == 'your_gemini_api_key_here':
    print("❌ GEMINI_API_KEY is still the placeholder value")
    print("   Edit .env and add your real API key from:")
    print("   https://aistudio.google.com/app/apikey")
    sys.exit(1)

GEMINI_WS_URL = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={GEMINI_API_KEY}"

print("=" * 60)
print("Gemini Live API Connection Test")
print("=" * 60)
print(f"API Key: {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-4:]}")
print(f"Model: {GEMINI_MODEL}")
print("")

async def test_connection():
    """Test WebSocket connection to Gemini"""

    print("Step 1: Creating SSL context...")
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        print("✅ SSL context created")
    except Exception as e:
        print(f"❌ SSL context error: {e}")
        return False

    print("\nStep 2: Connecting to Gemini WebSocket...")
    try:
        async with websockets.connect(GEMINI_WS_URL, ssl=ssl_context) as ws:
            print("✅ WebSocket connected!")

            print("\nStep 3: Sending setup message...")
            setup_msg = {
                "setup": {
                    "model": GEMINI_MODEL,
                    "generation_config": {
                        "response_modalities": ["AUDIO"],
                        "speech_config": {
                            "voice_config": {
                                "prebuilt_voice_config": {
                                    "voice_name": "Puck"
                                }
                            }
                        }
                    }
                }
            }

            await ws.send(json.dumps(setup_msg))
            print("✅ Setup message sent")

            print("\nStep 4: Waiting for setupComplete...")
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            response_data = json.loads(response)

            if response_data.get("setupComplete"):
                print("✅ Setup complete!")
                print("\n" + "=" * 60)
                print("SUCCESS! Gemini connection works!")
                print("=" * 60)
                print("\nYour voice chat should work now.")
                print("If the dashboard still fails, check:")
                print("1. Browser console for JavaScript errors")
                print("2. Terminal output when running dashboard.py")
                print("3. Network tab in browser DevTools")
                return True
            else:
                print(f"❌ Setup failed: {response_data}")
                return False

    except asyncio.TimeoutError:
        print("❌ Timeout waiting for Gemini response")
        print("   Check your internet connection")
        return False
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket connection rejected: {e}")
        print("   This usually means:")
        print("   - Invalid API key")
        print("   - API key doesn't have access to Gemini Live API")
        print("   - Network/firewall blocking connection")
        return False
    except Exception as e:
        print(f"❌ Connection error: {type(e).__name__}: {e}")
        return False

# Run test
try:
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
except KeyboardInterrupt:
    print("\n\nTest interrupted by user")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
