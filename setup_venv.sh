#!/bin/bash

# MorphStrike Virtual Environment Setup
# Simple setup script for when you're using a Python virtual environment

echo "🐍 MorphStrike Virtual Environment Setup"
echo "========================================"
echo ""

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ No virtual environment detected!"
    echo ""
    echo "Please create and activate a virtual environment first:"
    echo "  python3 -m venv morphstrike_env"
    echo "  source morphstrike_env/bin/activate"
    echo "  ./setup_venv.sh"
    echo ""
    exit 1
fi

echo "✅ Virtual environment detected: $VIRTUAL_ENV"
echo ""

# Install minimal Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements_simple.txt

if [ $? -eq 0 ]; then
    echo "✅ Python dependencies installed successfully"
else
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

echo ""
echo "🧪 Testing the installation..."

# Test basic imports
python3 -c "
import json, pathlib, datetime, threading
import requests, yaml
print('✅ All required modules imported successfully')
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Installation test passed"
else
    echo "❌ Installation test failed"
    exit 1
fi

echo ""
echo "🎉 Setup complete! You can now run:"
echo ""
echo "  # Test the framework"
echo "  python3 test_setup.py"
echo ""
echo "  # Start first-time setup"
echo "  ./start_first_time.sh"
echo ""
echo "  # Or manually start agents"
echo "  python3 morphstrike_framework.py agent_id role shared_dir"
echo ""

echo "📁 Next steps:"
echo "1. Run: python3 test_setup.py"
echo "2. If test passes, use: ./start_first_time.sh"
echo "3. Choose option 1 to test locally first"
echo ""