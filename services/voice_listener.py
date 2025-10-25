# Install
# pip install SpeechRecognition
# pip install pvporcupine pvrecorder
# brew install portaudio
# python3 -m pip install PyAudio

import pvporcupine
import pvrecorder
import speech_recognition as sr
import socketio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config import Config, Events

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

ACCESS_KEY = os.getenv("PORCUPINE_API_KEY")
CUSTOM_KEYWORD_NAME = 'Hey Helios' 
CUSTOM_KEYWORD_PATH = Path(__file__).parent / f"{CUSTOM_KEYWORD_NAME.lower().replace(' ', '_')}.ppn"

# WebSocket client for sending voice queries to the agent
sio = socketio.Client() 

def run_voice_assistant():
    """
    Run the voice assistant with Porcupine wake word detection.
    Listens for "computer" keyword, then captures speech and sends to agent.
    """
    # Connect to WebSocket server
    try:
        print(f"Connecting to WebSocket server at {Config.WEBSOCKET_SERVER_URL}...")
        sio.connect(Config.WEBSOCKET_SERVER_URL)
        print("Connected to WebSocket server!")
    except Exception as e:
        print(f"Failed to connect to WebSocket server: {e}")
        return

    # 1. Initialize Porcupine and Recorder
    # Available keywords: 'americano', 'computer', 'hey barista', 'terminator', 'pico clock',
    # 'grapefruit', 'porcupine', 'grasshopper', 'hey siri', 'picovoice', 'alexa',
    # 'ok google', 'jarvis', 'blueberry', 'hey google', 'bumblebee'

    ppn = pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=[str(CUSTOM_KEYWORD_PATH)]
    )

    recorder = pvrecorder.PvRecorder(frame_length=ppn.frame_length)
    r = sr.Recognizer()

    print(f"Listening for wake word 'computer'...")
    print(f"Say: 'computer' + [your question]")
    recorder.start()

    try:
        while True:
            # 2. Process Audio Frames for wake word
            pcm = recorder.read()
            keyword_index = ppn.process(pcm)

            # 3. Wake Word Detected
            if keyword_index >= 0:
                print("\n Wake word detected! Listening for your question...")
                recorder.stop()

                # Speech to Text
                try:
                    # Use the default microphone
                    with sr.Microphone() as source:
                        r.adjust_for_ambient_noise(source, duration=0.5)
                        audio = r.listen(source, timeout=5, phrase_time_limit=10)

                    # Use Google's STT for transcription
                    command_text = r.recognize_google(audio)
                    print(f"📝 You said: {command_text}")

                    # 4. Send query to agent via WebSocket
                    sio.emit('voice_query', {'query': command_text})
                    print(f"✅ Query sent to agent. Waiting for response...")

                    # Log to voice_log event for dashboard
                    sio.emit(Events.VOICE_LOG, {
                        'type': 'query',
                        'text': command_text,
                        'timestamp': int(pvrecorder.PvRecorder.get_audio_devices())
                    })

                except sr.WaitTimeoutError:
                    print("⏱️  No command received (timeout).")
                except sr.UnknownValueError:
                    print("❌ Could not understand audio.")
                except Exception as e:
                    print(f"❌ Error during command processing: {e}")

                print("\n👂 Listening for wake word 'computer' again...")
                recorder.start()  # Restart Porcupine listening

    except KeyboardInterrupt:
        print("\n\n👋 Shutting down voice assistant...")
    finally:
        recorder.stop()
        ppn.delete()
        recorder.delete()
        sio.disconnect()

# Call the function to run the assistant
if __name__ == '__main__':
    run_voice_assistant()
