"""
Flask Voice Chat Application - Gemini Live API Integration
Audio-to-Audio conversational AI with real-time WebSocket streaming

Two implementation approaches:
1. Threading-based (RECOMMENDED for Flask-sock stability)
2. Asyncio-based (Alternative approach)
"""
from flask import Flask, render_template, request
from flask_sock import Sock
from flask_cors import CORS
import websockets
import ssl
import certifi
import base64
import json
import os
import threading
import queue
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'voice_chat_dev_secret')
CORS(app)
sock = Sock(app)

# Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000')
GEMINI_MODEL = "models/gemini-2.5-flash-exp-native-audio-thinking-dialog"
GEMINI_WS_URL = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={GEMINI_API_KEY}"

# System instruction - customize the AI's personality here
SYSTEM_INSTRUCTION = {
    "parts": [{
        "text": """You are Helios, a friendly and helpful AI assistant specializing in solar energy,
        renewable energy systems, and environmental data analysis. You provide clear, concise
        answers and ask thoughtful follow-up questions.

        IMPORTANT: Ask ONE question at a time and WAIT for responses.
        Be conversational, natural, and engaging. Keep your responses brief and to the point."""
    }]
}


# ============================================================================
# APPROACH 1: THREADING-BASED (RECOMMENDED)
# ============================================================================

class GeminiVoiceConnection:
    """Manages WebSocket connection to Gemini with threading"""

    def __init__(self, client_ws):
        self.client_ws = client_ws
        self.gemini_ws = None
        self.client_to_gemini_queue = queue.Queue()
        self.gemini_to_client_queue = queue.Queue()
        self.running = False
        self.setup_complete = threading.Event()

    def connect_to_gemini(self):
        """Establish WebSocket connection to Gemini Live API"""
        try:
            # Create SSL context with certifi (CRITICAL for production)
            ssl_context = ssl.create_default_context(cafile=certifi.where())

            # Connect to Gemini WebSocket (synchronous)
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.gemini_ws = loop.run_until_complete(
                websockets.connect(GEMINI_WS_URL, ssl=ssl_context)
            )

            print("[Gemini] WebSocket connected")
            return True
        except Exception as e:
            print(f"[Gemini] Connection error: {e}")
            return False

    def send_setup_message(self):
        """Send initial setup configuration to Gemini"""
        try:
            setup_msg = {
                "setup": {
                    "model": GEMINI_MODEL,
                    "generation_config": {
                        "response_modalities": ["AUDIO"],
                        "speech_config": {
                            "voice_config": {
                                "prebuilt_voice_config": {
                                    "voice_name": "Puck"  # Options: Puck, Charon, Kore, Fenrir, Aoede
                                }
                            }
                        }
                    },
                    "system_instruction": SYSTEM_INSTRUCTION
                }
            }

            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.gemini_ws.send(json.dumps(setup_msg)))
            print("[Gemini] Setup message sent")

            # Wait for setupComplete
            response = loop.run_until_complete(self.gemini_ws.recv())
            response_data = json.loads(response)

            if response_data.get("setupComplete"):
                print("[Gemini] Setup complete")
                self.setup_complete.set()

                # Send initial prompt to start conversation
                initial_msg = {
                    "client_content": {
                        "turns": [{
                            "role": "user",
                            "parts": [{"text": "Hello! Introduce yourself briefly."}]
                        }],
                        "turn_complete": True
                    }
                }
                loop.run_until_complete(self.gemini_ws.send(json.dumps(initial_msg)))
                print("[Gemini] Initial prompt sent")
                return True
            else:
                print(f"[Gemini] Setup failed: {response_data}")
                return False

        except Exception as e:
            print(f"[Gemini] Setup error: {e}")
            return False

    def client_to_gemini_worker(self):
        """Thread: Forward audio from client to Gemini"""
        print("[Worker] Client->Gemini thread started")
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            while self.running:
                try:
                    # Get binary PCM data from client
                    audio_data = self.client_to_gemini_queue.get(timeout=0.1)

                    # Encode to base64 for JSON transmission
                    audio_b64 = base64.b64encode(audio_data).decode('utf-8')

                    # Send to Gemini with correct MIME type (CRITICAL!)
                    message = {
                        "realtime_input": {
                            "media_chunks": [{
                                "mime_type": "audio/pcm;rate=16000",  # Must specify rate!
                                "data": audio_b64
                            }]
                        }
                    }

                    loop.run_until_complete(self.gemini_ws.send(json.dumps(message)))

                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"[Worker] Client->Gemini error: {e}")
                    break

        finally:
            print("[Worker] Client->Gemini thread stopped")

    def gemini_to_client_worker(self):
        """Thread: Forward audio from Gemini to client"""
        print("[Worker] Gemini->Client thread started")
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            while self.running:
                try:
                    # Receive from Gemini
                    message = loop.run_until_complete(
                        asyncio.wait_for(self.gemini_ws.recv(), timeout=0.1)
                    )

                    data = json.loads(message)

                    # Extract audio from serverContent
                    if "serverContent" in data:
                        server_content = data["serverContent"]

                        # Check for model turn (contains audio)
                        if "modelTurn" in server_content:
                            parts = server_content["modelTurn"].get("parts", [])

                            for part in parts:
                                # Extract inline audio data
                                if "inlineData" in part:
                                    inline_data = part["inlineData"]
                                    audio_b64 = inline_data.get("data", "")

                                    if audio_b64:
                                        # Decode base64 to binary PCM
                                        audio_bytes = base64.b64decode(audio_b64)

                                        # Send binary PCM directly to client
                                        try:
                                            self.client_ws.send(audio_bytes)
                                        except Exception as e:
                                            print(f"[Worker] Send to client error: {e}")
                                            self.running = False
                                            break

                        # Log turn completion
                        if server_content.get("turnComplete"):
                            print("[Gemini] Turn complete")

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"[Worker] Gemini->Client error: {e}")
                    break

        finally:
            print("[Worker] Gemini->Client thread stopped")

    def start(self):
        """Start the bidirectional streaming"""
        self.running = True

        # Start worker threads
        client_thread = threading.Thread(target=self.client_to_gemini_worker, daemon=True)
        gemini_thread = threading.Thread(target=self.gemini_to_client_worker, daemon=True)

        client_thread.start()
        gemini_thread.start()

        # Wait for threads to complete
        client_thread.join()
        gemini_thread.join()

    def stop(self):
        """Stop the streaming and cleanup"""
        self.running = False
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.gemini_ws.close())
            print("[Gemini] WebSocket closed")
        except:
            pass


@sock.route('/ws/voice-chat')
def websocket_voice_chat(ws):
    """
    WebSocket endpoint for voice chat (Threading approach)
    """
    print(f"[Voice Chat] Client connected from {request.remote_addr}")

    # Check API key
    if not GEMINI_API_KEY:
        ws.send(json.dumps({"error": "GEMINI_API_KEY not configured"}))
        return

    # Create connection manager
    connection = GeminiVoiceConnection(ws)

    # Connect to Gemini
    if not connection.connect_to_gemini():
        ws.send(json.dumps({"error": "Failed to connect to Gemini"}))
        return

    # Send setup message
    if not connection.send_setup_message():
        ws.send(json.dumps({"error": "Gemini setup failed"}))
        return

    # Send ready signal to client
    ws.send(json.dumps({"status": "ready"}))

    # Start worker threads
    worker_thread = threading.Thread(target=connection.start, daemon=True)
    worker_thread.start()

    # Main loop: receive from client and queue for Gemini
    try:
        while True:
            data = ws.receive()

            if data is None:
                print("[Voice Chat] Client disconnected")
                break

            # Handle binary audio data
            if isinstance(data, bytes):
                connection.client_to_gemini_queue.put(data)

            # Handle JSON control messages
            elif isinstance(data, str):
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        ws.send(json.dumps({"type": "pong"}))
                except:
                    pass

    except Exception as e:
        print(f"[Voice Chat] Error: {e}")
    finally:
        connection.stop()
        print("[Voice Chat] Connection closed")


# ============================================================================
# APPROACH 2: ASYNCIO-BASED (ALTERNATIVE)
# ============================================================================

import asyncio

async def handle_voice_chat_async(client_ws):
    """
    Async handler for voice chat
    NOTE: This requires an async-compatible WebSocket library
    """
    print(f"[Voice Chat Async] Client connected")

    if not GEMINI_API_KEY:
        await client_ws.send(json.dumps({"error": "GEMINI_API_KEY not configured"}))
        return

    # Create SSL context
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # Connect to Gemini
    try:
        async with websockets.connect(GEMINI_WS_URL, ssl=ssl_context) as gemini_ws:
            print("[Gemini Async] Connected")

            # Send setup message
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
                    },
                    "system_instruction": SYSTEM_INSTRUCTION
                }
            }
            await gemini_ws.send(json.dumps(setup_msg))

            # Wait for setupComplete
            response = await gemini_ws.recv()
            response_data = json.loads(response)

            if not response_data.get("setupComplete"):
                await client_ws.send(json.dumps({"error": "Setup failed"}))
                return

            print("[Gemini Async] Setup complete")

            # Send initial prompt
            initial_msg = {
                "client_content": {
                    "turns": [{
                        "role": "user",
                        "parts": [{"text": "Hello! Introduce yourself briefly."}]
                    }],
                    "turn_complete": True
                }
            }
            await gemini_ws.send(json.dumps(initial_msg))

            # Send ready to client
            await client_ws.send(json.dumps({"status": "ready"}))

            # Bidirectional streaming with concurrent tasks
            async def client_to_gemini():
                """Forward client audio to Gemini"""
                try:
                    while True:
                        data = await client_ws.receive()

                        if isinstance(data, bytes):
                            audio_b64 = base64.b64encode(data).decode('utf-8')
                            message = {
                                "realtime_input": {
                                    "media_chunks": [{
                                        "mime_type": "audio/pcm;rate=16000",
                                        "data": audio_b64
                                    }]
                                }
                            }
                            await gemini_ws.send(json.dumps(message))
                except Exception as e:
                    print(f"[Async] Client->Gemini error: {e}")

            async def gemini_to_client():
                """Forward Gemini audio to client"""
                try:
                    while True:
                        message = await gemini_ws.recv()
                        data = json.loads(message)

                        if "serverContent" in data:
                            server_content = data["serverContent"]

                            if "modelTurn" in server_content:
                                parts = server_content["modelTurn"].get("parts", [])

                                for part in parts:
                                    if "inlineData" in part:
                                        audio_b64 = part["inlineData"].get("data", "")
                                        if audio_b64:
                                            audio_bytes = base64.b64decode(audio_b64)
                                            await client_ws.send(audio_bytes)

                            if server_content.get("turnComplete"):
                                print("[Gemini Async] Turn complete")

                except Exception as e:
                    print(f"[Async] Gemini->Client error: {e}")

            # Run both tasks concurrently
            await asyncio.gather(
                client_to_gemini(),
                gemini_to_client()
            )

    except Exception as e:
        print(f"[Voice Chat Async] Error: {e}")
        await client_ws.send(json.dumps({"error": str(e)}))


# Uncomment to use async approach (requires compatible WebSocket library)
# @sock.route('/ws/voice-chat-async')
# def websocket_voice_chat_async(ws):
#     asyncio.run(handle_voice_chat_async(ws))


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/voice')
def voice_chat():
    """Serve the voice chat page"""
    return render_template('voice_chat.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gemini_configured": GEMINI_API_KEY is not None,
        "timestamp": int(time.time())
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("Helios Voice Chat - Gemini Live API")
    print("=" * 70)
    print(f"Gemini API configured: {GEMINI_API_KEY is not None}")
    print(f"Voice Chat URL: http://localhost:5001/voice")
    print(f"WebSocket endpoint: ws://localhost:5001/ws/voice-chat")
    print("=" * 70)

    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )
