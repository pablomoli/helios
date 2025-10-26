#!/bin/bash
# Helios AI - Stop Script
# This script stops the dashboard

echo "🛑 Stopping Helios AI Dashboard..."
echo ""

# Kill dashboard
pkill -f "dashboard.py" && echo "✅ Dashboard stopped" || echo "⚠️  Dashboard not running"

echo ""
echo "✅ Helios AI stopped!"
