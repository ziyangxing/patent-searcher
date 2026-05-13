#!/bin/bash

echo "============================================"
echo "     Patent Searcher - AI Patent Search"
echo "============================================"
echo

# Check Python
PYTHON=""
if command -v python3 &> /dev/null; then PYTHON=python3
elif command -v python &> /dev/null; then PYTHON=python
else
    echo "[ERROR] Python 3.12+ is required but not found."
    echo "        Download: https://www.python.org/downloads/"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js 22+ is required but not found."
    echo "        Download: https://nodejs.org/"
    exit 1
fi

ROOT_DIR=$(pwd)

# Install frontend deps if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "[SETUP] Installing frontend dependencies (first time only)..."
    cd frontend && npm install && cd "$ROOT_DIR"
    echo "[SETUP] Done."
    echo
fi

# Check SerpAPI key
if ! grep -q "SERPAPI_KEY=." backend/.env 2>/dev/null; then
    echo
    echo "============================================"
    echo "  IMPORTANT: SerpAPI Key Required"
    echo "============================================"
    echo
    echo "  To search global patents, get a free key:"
    echo "  1. Open https://serpapi.com"
    echo "  2. Click 'Get Free API Key' and sign up"
    echo "  3. Copy your key"
    echo
    read -p "  Paste your SerpAPI key (or Enter to skip): " USER_KEY
    if [ -n "$USER_KEY" ]; then
        sed -i "s/SERPAPI_KEY=.*/SERPAPI_KEY=$USER_KEY/" backend/.env
        echo "  Key saved!"
    else
        echo "  Skipped. Will use local search mode only."
    fi
    echo
fi

# Install Python deps if needed
$PYTHON -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[SETUP] Installing Python dependencies (first time only)..."
    cd backend && pip install -r requirements.txt && cd "$ROOT_DIR"
    echo "[SETUP] Done."
    echo
fi

# Build FAISS index if needed
if [ ! -f "backend/data/faiss_index.bin" ]; then
    echo "[SETUP] Building patent index (first time only)..."
    cd backend && $PYTHON -m app.services.data_importer && cd "$ROOT_DIR"
    echo
fi

echo "[1/2] Starting backend server (loading AI model, ~20s first time)..."
$PYTHON backend/run_server.py &
BACKEND_PID=$!

echo "      Waiting for backend..."
until curl -s http://localhost:8766/api/health > /dev/null 2>&1; do sleep 3; done
echo "      Backend ready!"

echo "[2/2] Starting frontend..."
cd frontend && npm run dev &
FRONTEND_PID=$!
cd "$ROOT_DIR"

echo "      Waiting for frontend..."
until curl -s http://localhost:3000 > /dev/null 2>&1; do sleep 2; done
echo "      Frontend ready!"

echo
echo "============================================"
echo "     All systems ready!"
echo "     Opening browser..."
echo "============================================"

if command -v open &> /dev/null; then
    open http://localhost:3000/search
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000/search
fi

echo
echo "Press Enter to stop all services..."
read

kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
echo "Services stopped."
