#!/bin/bash
# Helios AI - Quick Start Script
# This script starts both the dashboard and the Gemini voice agent

echo "========================================"
echo "  Starting Helios AI System"
echo "========================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found!"
    echo "   Please run: python -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Copy .env.example to .env and add your API keys"
fi

echo "🚀 Starting Helios AI Dashboard on http://localhost:5000"
echo "   (Everything runs in the dashboard - no separate services!)"
echo ""

# Start dashboard in background with nohup
cd dashboard
nohup ../.venv/bin/python dashboard.py > /tmp/helios_dashboard.log 2>&1 &
DASHBOARD_PID=$!
cd ..

echo "   Dashboard starting (PID: $DASHBOARD_PID)..."
sleep 5

# Check if process is running (give it time to fully start)
if ps -p $DASHBOARD_PID > /dev/null; then
    echo "   ✅ Dashboard running"
else
    echo "   ❌ Dashboard failed to start - check /tmp/helios_dashboard.log"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ Helios AI is running!"
echo "========================================"
echo ""
echo "📊 Dashboard: http://localhost:5000"
echo "   - View solar tracker data"
echo "   - Click 🎤 button to start voice control"
echo "   - Say 'Helios' followed by your question"
echo "   - Watch the spectrogram visualize your voice!"
echo ""
echo "📝 Logs:"
echo "   tail -f /tmp/helios_dashboard.log"
echo ""
echo "🛑 To stop:"
echo "   ./stop_helios.sh"
echo "   OR manually: pkill -f dashboard.py"
echo ""
echo "========================================"
echo "PID: Dashboard=$DASHBOARD_PID"
echo ""
echo "💡 Everything runs in one service - just open the dashboard!"
echo ""
