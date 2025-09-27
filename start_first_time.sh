#!/bin/bash

# MorphStrike First-Time Setup Script
# This script helps you get your first two agents running

echo "🚀 MorphStrike First-Time Setup"
echo "================================="
echo ""

# Check if we're in the right directory
if [ ! -f "morphstrike_framework.py" ]; then
    echo "❌ Error: morphstrike_framework.py not found"
    echo "Please run this script from the MorphStrike directory"
    exit 1
fi

echo "What would you like to do?"
echo ""
echo "1) Test the framework locally (single machine)"
echo "2) Start VM1 (Server + Giver agent)"
echo "3) Start VM2 (Taker agent) - connect to existing server"
echo "4) Run diagnostics"
echo ""
read -p "Choose option (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🧪 Running local test..."
        echo "This will test both agents on this machine"
        echo ""
        python3 test_setup.py
        ;;
    
    2)
        echo ""
        echo "🖥️  Setting up VM1 (Server + Giver)"
        echo ""
        
        # Create shared directory
        SHARED_DIR="./morphstrike_shared"
        mkdir -p "$SHARED_DIR"
        
        # Get target IP for CTF
        read -p "Enter CTF target IP (or press Enter for test mode): " TARGET_IP
        
        echo ""
        echo "Starting HTTP server for file sharing..."
        echo "Press Ctrl+C to stop the server when done"
        echo ""
        
        # Start server in background
        python3 server_setup.py --shared-dir "$SHARED_DIR" --port 8080 &
        SERVER_PID=$!
        
        # Wait a moment for server to start
        sleep 3
        
        # Get local IP
        LOCAL_IP=$(hostname -I | awk '{print $1}')
        
        echo ""
        echo "✅ Server started! Connection info:"
        echo "   Local IP: $LOCAL_IP"
        echo "   Port: 8080"
        echo "   Shared directory: $SHARED_DIR"
        echo ""
        echo "On VM2, use this command:"
        echo "   python3 morphstrike_framework.py taker_01 taker http://$LOCAL_IP:8080/"
        echo ""
        echo "Press Enter when VM2 is ready, then I'll start the Giver agent..."
        read
        
        echo "Starting Giver agent..."
        if [ -n "$TARGET_IP" ]; then
            python3 morphstrike_framework.py giver_01 giver "$SHARED_DIR" "$TARGET_IP"
        else
            python3 morphstrike_framework.py giver_01 giver "$SHARED_DIR"
        fi
        
        # Clean up
        kill $SERVER_PID 2>/dev/null
        ;;
    
    3)
        echo ""
        echo "🖥️  Setting up VM2 (Taker Agent)"
        echo ""
        
        read -p "Enter VM1's IP address: " VM1_IP
        read -p "Enter port (default 8080): " PORT
        PORT=${PORT:-8080}
        
        echo ""
        echo "Connecting to http://$VM1_IP:$PORT/"
        echo "Starting Taker agent..."
        echo ""
        
        python3 morphstrike_framework.py taker_01 taker "http://$VM1_IP:$PORT/"
        ;;
    
    4)
        echo ""
        echo "🔍 Running diagnostics..."
        echo ""
        
        echo "Checking Python version:"
        python3 --version
        echo ""
        
        echo "Checking required files:"
        for file in morphstrike_framework.py server_setup.py hexstrike_integration.py; do
            if [ -f "$file" ]; then
                echo "✅ $file"
            else
                echo "❌ $file (missing)"
            fi
        done
        echo ""
        
        echo "Checking Python modules:"
        python3 -c "import json, pathlib, datetime, threading; print('✅ Core modules OK')" 2>/dev/null || echo "❌ Core modules missing"
        python3 -c "import yaml; print('✅ PyYAML OK')" 2>/dev/null || echo "❌ PyYAML missing (pip3 install pyyaml)"
        python3 -c "import requests; print('✅ Requests OK')" 2>/dev/null || echo "❌ Requests missing (pip3 install requests)"
        echo ""
        
        echo "Checking network connectivity:"
        if command -v nc >/dev/null 2>&1; then
            echo "✅ netcat available for network testing"
        else
            echo "❌ netcat not available (install with: sudo apt install netcat)"
        fi
        
        echo ""
        echo "To install missing dependencies:"
        echo "   pip3 install pyyaml requests"
        ;;
    
    *)
        echo "Invalid option. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "Done! Check the logs in ./morphstrike_shared/logs/ for debugging."