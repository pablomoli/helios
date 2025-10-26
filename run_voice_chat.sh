#!/bin/bash
#
# Quick start script for Helios Voice Chat
# Runs the voice chat server with proper environment setup
#

set -e  # Exit on error

echo "=============================================="
echo "  Helios Voice Chat - Quick Start"
echo "=============================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "✅ .env created!"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your GEMINI_API_KEY"
    echo "   Get your key at: https://aistudio.google.com/app/apikey"
    echo ""
    echo "Press Enter when ready to continue..."
    read
fi

# Check if GEMINI_API_KEY is set
if ! grep -q "^GEMINI_API_KEY=.\+" .env; then
    echo "⚠️  GEMINI_API_KEY not configured in .env"
    echo ""
    echo "Please edit .env and add your Gemini API key:"
    echo "   GEMINI_API_KEY=your_actual_key_here"
    echo ""
    echo "Get your key at: https://aistudio.google.com/app/apikey"
    echo ""
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "📦 Virtual environment not found."
    echo "Do you want to create one? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
        echo "✅ Virtual environment created!"
        echo ""
    fi
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment (venv)..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "🔧 Activating virtual environment (.venv)..."
    source .venv/bin/activate
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python -c "import flask_sock" 2>/dev/null; then
    echo "⚠️  Dependencies not installed."
    echo "Installing from requirements.txt..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed!"
    echo ""
fi

echo ""
echo "=============================================="
echo "  Starting Voice Chat Server..."
echo "=============================================="
echo ""
echo "📍 Server will run on: http://localhost:5001"
echo "🎤 Voice Chat UI: http://localhost:5001/voice"
echo "🔌 WebSocket: ws://localhost:5001/ws/voice-chat"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "=============================================="
echo ""

# Run the voice chat server
cd dashboard
python voice_chat.py
