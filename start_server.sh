#!/bin/bash
# Simple script to start the Int Crucible API server

set -e

echo "Starting Int Crucible API server..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Please run ./setup_backend.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠ Warning: .env file not found. Creating minimal .env..."
    echo "DATABASE_URL=sqlite:///crucible.db" > .env
    echo "LOG_LEVEL=INFO" >> .env
    echo "API_HOST=127.0.0.1" >> .env
    echo "API_PORT=8000" >> .env
fi

echo "Server starting on http://127.0.0.1:8000"
echo "API documentation: http://127.0.0.1:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Start the server
python -m crucible.api.main

