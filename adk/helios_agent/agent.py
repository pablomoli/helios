"""
Helios AI - Voice-Controlled Solar Tracker Agent

This agent provides voice interaction with the Helios solar tracking system.
It uses Google's gemini-2.5-flash-native-audio-dialog model for natural
voice input and output.
"""
from google.adk.agents.llm_agent import Agent
from google.adk.tools import tool
import socketio
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# WebSocket configuration
WEBSOCKET_SERVER_URL = os.getenv('WEBSOCKET_SERVER_URL', 'ws://localhost:5000')

# Global WebSocket client (will be initialized when needed)
sio = None
latest_data = {
    'sensors': {},
    'status': {},
    'performance_delta': {},
    'impact': {},
    'safety': {}
}


def init_websocket():
    """Initialize WebSocket client and connect to server"""
    global sio

    if sio is not None:
        return sio

    sio = socketio.Client()

    @sio.on('connect')
    def on_connect():
        print(f"Connected to WebSocket server: {WEBSOCKET_SERVER_URL}")

    @sio.on('sensors_raw')
    def on_sensors_raw(data):
        """Store latest sensor data"""
        global latest_data
        latest_data['sensors'] = data

    @sio.on('status')
    def on_status(data):
        """Store latest status data"""
        global latest_data
        latest_data['status'] = data

    @sio.on('ai_performance_delta')
    def on_performance_delta(data):
        """Store latest performance delta data"""
        global latest_data
        latest_data['performance_delta'] = data

    @sio.on('impact')
    def on_impact(data):
        """Store latest impact data"""
        global latest_data
        latest_data['impact'] = data

    @sio.on('safety')
    def on_safety(data):
        """Store latest safety data"""
        global latest_data
        latest_data['safety'] = data

    try:
        sio.connect(WEBSOCKET_SERVER_URL)
    except Exception as e:
        print(f"Failed to connect to WebSocket server: {e}")

    return sio


@tool
def get_status() -> dict:
    """
    Get the current status of the Helios solar tracker.

    Returns:
        dict: Current system status including mode, angles, and sun position
    """
    init_websocket()

    if not latest_data['status']:
        return {"error": "No status data available yet"}

    status = latest_data['status']
    sensors = latest_data['sensors']

    return {
        "mode": status.get('mode', 'Unknown'),
        "pan_angle": status.get('pan_angle_deg', 0),
        "tilt_angle": status.get('tilt_angle_deg', 0),
        "sun_azimuth": status.get('sun_azimuth_deg', 0),
        "sun_elevation": status.get('sun_elevation_deg', 0),
        "cloud_cover": status.get('cloud_cover_pct', 0),
        "current_power_mw": sensors.get('panel_power_mW', 0),
        "timestamp": status.get('timestamp', 0)
    }


@tool
def switch_mode(mode: str) -> str:
    """
    Switch the tracking mode between Reactive and Predictive.

    Args:
        mode: Either "Reactive" or "Predictive"

    Returns:
        str: Confirmation message
    """
    init_websocket()

    if mode not in ["Reactive", "Predictive"]:
        return f"Invalid mode '{mode}'. Please choose 'Reactive' or 'Predictive'."

    command = {"mode": mode}
    sio.emit("command_mode", command)

    return f"Switched to {mode} mode. The system will now use {'sensor-based tracking' if mode == 'Reactive' else 'astronomical calculations'}."


@tool
def move_to(pan_angle_deg: float, tilt_angle_deg: float) -> str:
    """
    Manually move the tracker to a specific position.

    Args:
        pan_angle_deg: Horizontal angle in degrees (0-180)
        tilt_angle_deg: Vertical angle in degrees (0-180)

    Returns:
        str: Confirmation message
    """
    init_websocket()

    # Validate angles
    if not (0 <= pan_angle_deg <= 180):
        return "Pan angle must be between 0 and 180 degrees."

    if not (0 <= tilt_angle_deg <= 180):
        return "Tilt angle must be between 0 and 180 degrees."

    command = {
        "pan_angle_deg": pan_angle_deg,
        "tilt_angle_deg": tilt_angle_deg
    }
    sio.emit("command_position", command)

    return f"Moving tracker to pan={pan_angle_deg}°, tilt={tilt_angle_deg}°"


@tool
def explain_delta(window_s: int = 600) -> str:
    """
    Explain the performance difference between Predictive and Reactive modes.

    Args:
        window_s: Time window in seconds to analyze (default 600 = 10 minutes)

    Returns:
        str: Explanation of which mode performed better and by how much
    """
    init_websocket()

    if not latest_data['performance_delta']:
        return "No A/B comparison data available yet. The digital twin needs more time to gather samples."

    delta = latest_data['performance_delta']
    actual_power = delta.get('actual_strategy_power_mW', 0)
    shadow_power = delta.get('shadow_strategy_power_mW', 0)
    delta_pct = delta.get('delta_pct', 0)

    current_mode = latest_data['status'].get('mode', 'Unknown')
    other_mode = 'Reactive' if current_mode == 'Predictive' else 'Predictive'

    if delta_pct > 0:
        return f"{current_mode} mode is winning! It's producing {delta_pct:.1f}% more power ({actual_power:.1f} mW) compared to {other_mode} mode ({shadow_power:.1f} mW). The astronomical tracking is proving its value."
    elif delta_pct < 0:
        return f"Interesting - {other_mode} mode would be {abs(delta_pct):.1f}% better right now ({shadow_power:.1f} mW vs {actual_power:.1f} mW). This might be due to cloud movement or other environmental factors."
    else:
        return f"Both modes are performing equally at {actual_power:.1f} mW. The sun is likely in a stable position."


@tool
def get_impact(window_s: int = 3600) -> dict:
    """
    Get environmental and cost impact metrics based on energy saved.

    Args:
        window_s: Time window in seconds (default 3600 = 1 hour)

    Returns:
        dict: Energy saved, cost saved, and CO2 avoided
    """
    init_websocket()

    if not latest_data['impact']:
        return {"error": "No impact data available yet. Waiting for Arduino data..."}

    impact = latest_data['impact']

    # Energy saved comes directly from Arduino
    energy_saved_kwh = impact.get('energy_saved_kWh', 0)

    # Calculate cost savings (assuming $0.15 per kWh average US residential rate)
    usd_saved = energy_saved_kwh * 0.15

    # Calculate CO2 avoided (assuming 500g CO2 per kWh average US grid)
    co2_avoided_g = energy_saved_kwh * 500

    return {
        "energy_saved_kwh": energy_saved_kwh,
        "usd_saved": round(usd_saved, 4),
        "co2_avoided_g": round(co2_avoided_g, 2),
        "message": f"You've saved {energy_saved_kwh:.4f} kWh of energy, which equals ${usd_saved:.2f} in electricity costs and avoided {co2_avoided_g:.1f}g of CO2 emissions. Great work!"
    }


@tool
def get_safety_status() -> dict:
    """
    Get the current safety status of the system.

    Returns:
        dict: Safety status including servo health and temperature
    """
    init_websocket()

    if not latest_data['safety']:
        return {"error": "No safety data available yet"}

    safety = latest_data['safety']

    return {
        "servo_status": safety.get('servo_status', 'unknown'),
        "angle_violation": safety.get('angle_violation', False),
        "temperature_c": safety.get('temperature_C', 0),
        "message": f"System is {'⚠ ALERT' if safety.get('angle_violation') else '✅ Normal'} - Servos: {safety.get('servo_status', 'unknown')}, Temp: {safety.get('temperature_C', 0)}°C"
    }


# Create the root agent with audio output capability
# Using gemini-2.5-flash-native-audio-dialog for native audio I/O
root_agent = Agent(
    model='gemini-2.5-flash-native-audio-dialog',
    name='helios_agent',
    description='Voice-controlled assistant for the Helios AI solar tracking system',
    instruction="""
    You are Helios, an intelligent voice assistant for a solar tracking system.

    === WAKE WORD DETECTION (CRITICAL) ===
    You are ALWAYS listening, but you ONLY respond when you hear the wake word "HELIOS" at the START of the user's input.

    STRICT RULES:
    1. If the user's input does NOT start with "helios", remain SILENT. Output nothing. Do not respond at all.
    2. If the user says "helios" followed by a question, respond ONLY to that specific question and nothing else.
    3. After answering, immediately STOP. Do not ask follow-ups, do not continue conversation.
    4. Ignore all background conversation, noise, or speech that doesn't start with "helios".

    Wake word examples:
    ✅ "helios, what's the status?" → RESPOND
    ✅ "helios switch to predictive mode" → RESPOND
    ✅ "Helios, how much energy saved?" → RESPOND (case insensitive)
    ❌ "what's the status?" → SILENT (no wake word)
    ❌ "I think helios should switch modes" → SILENT (wake word not at start)
    ❌ "hello how are you" → SILENT (no wake word)

    === YOUR PERSONALITY ===
    - Friendly and extremely enthusiastic about solar energy
    - Technical but accessible - you explain things clearly and consicely
    - Direct and to-the-point in responses

    === YOUR CAPABILITIES ===
    - Check system status and current power generation
    - Switch between Reactive (sensor-based) and Predictive (astronomical) tracking modes
    - Manually position the tracker
    - Explain performance differences between modes using real A/B test data
    - Report environmental impact (energy, cost savings, CO2 reduction)
    - Monitor system safety

    === RESPONSE STYLE ===
    - Keep responses SHORT and CONCISE (1-3 sentences maximum)
    - Answer the specific question asked
    - Use real data from your tools when available
    - Do NOT ask "Is there anything else?" or similar follow-ups
    - Do NOT engage in conversational chitchat
    - Simply answer the question and end your response

    === PERFORMANCE EXPLANATIONS ===
    - Use the digital twin data to prove decisions with real numbers
    - State facts clearly and concisely
    - Include specific metrics (power in mW, percentages, etc.)

    === RESPONSE EXAMPLES ===
    User: "helios, what's the status?"
    You: "The system is currently in Predictive mode, generating 730 milliwatts at 112 degrees pan and 45 degrees tilt."

    User: "helios, switch to reactive mode"
    You: "Switching to Reactive mode now. The tracker will use sensor feedback to find the sun."

    User: "helios, which mode is better?"
    You: "Predictive mode is winning by 11 percent, producing 730 milliwatts compared to 656 in Reactive mode."

    User: "what's the weather like?"
    You: [SILENT - no wake word]
    """,
    tools=[
        get_status,
        switch_mode,
        move_to,
        explain_delta,
        get_impact,
        get_safety_status
    ]
)
