#!/bin/bash

# OCR Service Startup Script

# Change to the script directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
fi

# Set default port if not set
export PORT=${PORT:-8001}
export HOST=${HOST:-0.0.0.0}

echo "Starting OCR Service on $HOST:$PORT"
echo "Make sure dependencies are installed: pip install -r requirements.txt"

python main.py
