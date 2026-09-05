#!/bin/bash

# Function to handle cleanup on exit
cleanup() {
    echo "Stopping all services..."
    kill $PID_BACKTEST $PID_NLBACKEND $PID_FRONTEND
    exit 0
}

# Trap SIGINT (Ctrl+C) and call cleanup
trap cleanup SIGINT

echo "========================================"
echo "Starting TradeKaro / NLconverter Stack"
echo "========================================"

# Determine the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# 1. Start Backtesting Engine Backend
echo "-> Starting Backtesting Engine Backend (Port 8002)..."
(
    cd "$SCRIPT_DIR/../../BackTesting/Backtesting_Engine" || { echo "Backtesting_Engine directory not found"; exit 1; }
    export BACKTEST_API_TOKEN="9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    fi
    exec python -m uvicorn app.api.server:app --reload --port 8002 --host 0.0.0.0
) &
PID_BACKTEST=$!

# 2. Start NLconverter Backend
echo "-> Starting NLconverter Backend (Port 8000)..."
(
    cd "$SCRIPT_DIR/backend" || { echo "NLconverter/backend directory not found"; exit 1; }
    export BACKTEST_ENGINE_API_KEY="9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    fi
    exec python -m uvicorn main:app --reload --port 8000 --host 0.0.0.0
) &
PID_NLBACKEND=$!

# 3. Start NLconverter Frontend
echo "-> Starting NLconverter Frontend (Next.js)..."
(
    cd "$SCRIPT_DIR/frontend" || { echo "NLconverter/frontend directory not found"; exit 1; }
    exec npm run dev
) &
PID_FRONTEND=$!

echo "========================================"
echo "All services are running!"
echo "Backtesting Engine : http://localhost:8002"
echo "NLconverter Backend: http://localhost:8000"
echo "NLconverter Frontend: http://localhost:3000"
echo "(Press Ctrl+C to stop all services)"
echo "========================================"

# Wait for all background processes
wait $PID_BACKTEST
wait $PID_NLBACKEND
wait $PID_FRONTEND
