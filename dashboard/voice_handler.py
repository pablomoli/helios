"""
Voice Handler for Dashboard
Integrates Gemini 2.5 Flash Native Audio Dialog directly into the dashboard
"""
import os
import sys
from pathlib import Path
import google.generativeai as genai
from config import Config

# Configure Gemini API
genai.configure(api_key=Config.GOOGLE_GENAI_API_KEY)

# Initialize the model with native audio dialog
model = genai.GenerativeModel('gemini-2.5-flash-native-audio-dialog')

# Store latest system data for agent context
latest_system_data = {
    'sensors': {},
    'status': {},
    'impact': {},
    'safety': {},
    'performance_delta': {}
}


def update_system_data(data_type, data):
    """Update the latest system data from WebSocket events"""
    global latest_system_data
    latest_system_data[data_type] = data


def get_system_context():
    """Get current system context as a formatted string"""
    sensors = latest_system_data.get('sensors', {})
    status = latest_system_data.get('status', {})
    impact = latest_system_data.get('impact', {})
    safety = latest_system_data.get('safety', {})

    context = f"""
Current Solar Tracker Status:
- Mode: {status.get('mode', 'Unknown')}
- Power Output: {sensors.get('panel_power_mW', 0):.1f} mW
- Panel Voltage: {sensors.get('panel_voltage_V', 0):.2f} V
- Panel Current: {sensors.get('panel_current_mA', 0):.1f} mA
- Pan Angle: {status.get('pan_angle_deg', 0):.1f}°
- Tilt Angle: {status.get('tilt_angle_deg', 0):.1f}°
- Energy Saved: {impact.get('energy_saved_kWh', 0):.4f} kWh
- Safety Status: {safety.get('servo_status', 'Unknown')}
"""
    return context.strip()


def process_voice_query(audio_data, wake_word_detected=False):
    """
    Process voice query using Gemini

    Args:
        audio_data: Base64 encoded audio data
        wake_word_detected: Whether "Helios" was detected

    Returns:
        dict with response text and audio
    """
    try:
        # Check if wake word was detected
        if not wake_word_detected:
            return {
                'success': False,
                'message': 'Wake word "Helios" not detected',
                'should_respond': False
            }

        # Get current system context
        context = get_system_context()

        print(f"[Voice] Processing query with context: {context[:100]}...")

        # For now, return a simple test response
        # TODO: Implement actual audio transcription and processing
        response_text = f"I'm Helios, your solar tracking assistant. The system is currently in {latest_system_data.get('status', {}).get('mode', 'Unknown')} mode, generating {latest_system_data.get('sensors', {}).get('panel_power_mW', 0):.1f} milliwatts."

        print(f"[Voice] Generated response: {response_text}")

        return {
            'success': True,
            'response_text': response_text,
            'should_respond': True
        }

    except Exception as e:
        print(f"Error processing voice query: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'message': 'Error processing voice query',
            'should_respond': False
        }


def simple_wake_word_detection(audio_data):
    """
    Simple wake word detection using Gemini

    Args:
        audio_data: Audio data to analyze

    Returns:
        bool: True if "Helios" was detected at the start
    """
    try:
        # For now, always return True to test the response
        # We'll add proper wake word detection later
        print("[Voice] Wake word check - SKIPPING for testing (always True)")
        return True

    except Exception as e:
        print(f"Wake word detection error: {e}")
        return False
