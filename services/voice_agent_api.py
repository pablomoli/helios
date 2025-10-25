"""
Voice Agent API Service
Provides WebSocket API for the Helios agent with cross-platform TTS support
Receives text queries → Agent processing → Audio response (Windows/Linux/macOS)
"""
import sys
import os
from pathlib import Path
from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import pyttsx3

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'adk'))

from config.config import Config, Events

# Import the ADK agent tools
try:
    from helios_agent.agent import (
        get_status, switch_mode, move_to,
        explain_delta, get_impact, get_safety_status
    )
    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import agent tools: {e}")
    AGENT_AVAILABLE = False

# Flask app
app = Flask(__name__)
CORS(app)
socketio_server = SocketIO(app, cors_allowed_origins="*")

# Initialize cross-platform TTS engine
tts_engine = None


def init_tts():
    """Initialize the TTS engine (cross-platform)"""
    global tts_engine
    try:
        tts_engine = pyttsx3.init()
        # Configure voice properties
        tts_engine.setProperty('rate', 175)  # Speed of speech (words per minute)
        tts_engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)

        # Optional: Set voice (uncomment to use specific voice)
        # voices = tts_engine.getProperty('voices')
        # tts_engine.setProperty('voice', voices[0].id)  # 0 = male, 1 = female (usually)

        print("✅ TTS engine initialized successfully")
        return True
    except Exception as e:
        print(f"❌ TTS initialization failed: {e}")
        return False


def speak(text):
    """Speak text using cross-platform TTS (Windows/Linux/macOS)"""
    global tts_engine

    if tts_engine is None:
        if not init_tts():
            print(f"🔊 TTS not available. Text response: {text}")
            return False

    try:
        print(f"🔊 Speaking: {text}")
        tts_engine.say(text)
        tts_engine.runAndWait()
        return True
    except Exception as e:
        print(f"❌ TTS error: {e}")
        print(f"🔊 Text fallback: {text}")
        return False


@socketio_server.on('voice_query')
def handle_voice_query(data):
    """
    WebSocket endpoint for voice queries
    Receives: {"query": "what is the status?"}
    Processes with agent tools and speaks response
    """
    query_text = data.get('query', '')

    if not query_text:
        emit('voice_response', {'error': 'No query provided'})
        return

    print(f"\n🎤 Voice Query: {query_text}")

    try:
        if not AGENT_AVAILABLE:
            response_text = "Agent tools are not available. Please check the setup."
            speak(response_text)
            emit('voice_response', {'query': query_text, 'response': response_text, 'error': True})
            return

        # Process query based on keywords
        response_text = ""

        if 'status' in query_text.lower():
            status = get_status()
            if 'error' in status:
                response_text = status['error']
            else:
                response_text = f"The system is in {status['mode']} mode, generating {status['current_power_mw']:.0f} milliwatts. Pan angle is {status['pan_angle']:.0f} degrees, tilt is {status['tilt_angle']:.0f} degrees."

        elif 'switch' in query_text.lower() or 'change' in query_text.lower():
            if 'predictive' in query_text.lower():
                response_text = switch_mode('Predictive')
            elif 'reactive' in query_text.lower():
                response_text = switch_mode('Reactive')
            else:
                response_text = "Please specify either Predictive or Reactive mode."

        elif 'move' in query_text.lower() or 'position' in query_text.lower():
            # Simple position parsing (you can enhance this)
            response_text = "Manual positioning requires specific pan and tilt angles. Please use the dashboard for precise control."

        elif 'impact' in query_text.lower() or 'energy' in query_text.lower() or 'saved' in query_text.lower() or 'environment' in query_text.lower():
            impact = get_impact()
            if 'error' in impact:
                response_text = impact['error']
            else:
                response_text = impact.get('message', str(impact))

        elif 'safety' in query_text.lower() or 'safe' in query_text.lower():
            safety = get_safety_status()
            if 'error' in safety:
                response_text = safety['error']
            else:
                response_text = safety.get('message', str(safety))

        elif 'performance' in query_text.lower() or 'compare' in query_text.lower() or 'comparison' in query_text.lower() or 'delta' in query_text.lower() or 'better' in query_text.lower():
            response_text = explain_delta()

        else:
            response_text = "I can help with system status, mode switching, impact metrics, safety monitoring, and performance comparisons. What would you like to know?"

        print(f"🤖 Response: {response_text}")

        # Speak the response (cross-platform)
        speak(response_text)

        # Send response back via WebSocket
        emit('voice_response', {
            'query': query_text,
            'response': response_text
        })

        # Log to voice_log for dashboard
        socketio_server.emit(Events.VOICE_LOG, {
            'type': 'response',
            'text': response_text
        })

    except Exception as e:
        print(f"❌ Error processing query: {e}")
        error_msg = "Sorry, I encountered an error processing your request."
        speak(error_msg)
        emit('voice_response', {'error': str(e), 'response': error_msg})


@socketio_server.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print("✅ Voice listener connected to agent API")


@socketio_server.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print("👋 Voice listener disconnected from agent API")


@app.route('/')
def index():
    """Status page"""
    platform_info = {
        'win32': 'Windows SAPI',
        'linux': 'espeak',
        'darwin': 'macOS NSSpeechSynthesizer'
    }.get(sys.platform, 'Unknown')

    return f"""
    <html>
    <head><title>Helios Voice Agent API</title></head>
    <body style="font-family: Arial, sans-serif; margin: 40px;">
        <h1>🎙️ Helios Voice Agent API</h1>
        <p><strong>Agent Status:</strong> {'✅ Ready' if AGENT_AVAILABLE else '❌ Not Available'}</p>
        <p><strong>TTS Engine:</strong> {'✅ ' + platform_info if tts_engine else '❌ Not Initialized'}</p>
        <p><strong>WebSocket:</strong> ws://localhost:{Config.DASHBOARD_PORT}</p>
        <hr>
        <h2>How to Use:</h2>
        <ol>
            <li>Run this service: <code>python services/voice_agent_api.py</code></li>
            <li>Run voice listener: <code>python services/voice_listener.py</code></li>
            <li>Say: <strong>"computer"</strong> + your question</li>
        </ol>
        <h3>Example Questions:</h3>
        <ul>
            <li>"What's the status?"</li>
            <li>"Switch to predictive mode"</li>
            <li>"How much energy have we saved?"</li>
            <li>"Is the system safe?"</li>
            <li>"Compare the performance"</li>
        </ul>
    </body>
    </html>
    """


def main():
    """Start the voice agent API service"""
    print("=" * 70)
    print("🎙️  Helios Voice Agent API - Cross-Platform Edition")
    print("=" * 70)
    print(f"📡 WebSocket Server: ws://localhost:{Config.DASHBOARD_PORT}")
    print(f"🌐 Web Interface: http://localhost:{Config.DASHBOARD_PORT}")
    print(f"🤖 Agent Tools: {'✅ Available' if AGENT_AVAILABLE else '❌ Not Available'}")

    # Initialize TTS
    if init_tts():
        platform_name = {
            'win32': 'Windows SAPI',
            'linux': 'espeak/Festival',
            'darwin': 'macOS NSSpeechSynthesizer'
        }.get(sys.platform, sys.platform)
        print(f"🔊 TTS Engine: ✅ {platform_name}")
    else:
        print(f"🔊 TTS Engine: ❌ Failed to initialize")
        print("   Install requirements: pip install pyttsx3")
        if sys.platform == 'linux':
            print("   Linux users: sudo apt-get install espeak")

    print("=" * 70)
    print("\n👂 Waiting for voice queries from voice_listener.py...")
    print("   Say 'computer' + your question to interact\n")
    print("=" * 70)

    # Run the WebSocket server
    socketio_server.run(
        app,
        host='0.0.0.0',
        port=Config.DASHBOARD_PORT,
        debug=False,
        allow_unsafe_werkzeug=True
    )


if __name__ == "__main__":
    main()
