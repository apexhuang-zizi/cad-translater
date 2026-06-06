#!/bin/bash
echo "============================================"
echo "  CAD Translator - Starting Server"
echo "============================================"

cd "$(dirname "$0")"

# Check Python
python3 --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Python3 not found. Please install Python 3.9+"
    exit 1
fi

# Install dependencies
echo "Checking dependencies..."
pip3 install -r requirements.txt -q

# Start server
echo ""
echo "Starting server at http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""
python3 app.py
