#!/bin/bash
set -e

echo
echo "============================================"
echo "  Patent Searcher - AI Global Patent Search"
echo "============================================"
echo

# Find Python
PYTHON=""
if command -v python3 &>/dev/null; then PYTHON=python3
elif command -v python &>/dev/null; then PYTHON=python
else
    echo "[ERROR] Python 3.12+ not found."
    echo "        https://www.python.org/downloads/"
    exit 1
fi

# Check Node
if ! command -v node &>/dev/null; then
    echo "[ERROR] Node.js not found."
    echo "        https://nodejs.org/"
    exit 1
fi

ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$ROOT"

# Install frontend deps
if [ ! -d "frontend/node_modules" ]; then
    echo "[SETUP] Installing frontend dependencies..."
    cd frontend && npm install && cd "$ROOT"
fi

# Create .env from example if missing
if [ ! -f "backend/.env" ]; then
    echo "[SETUP] Creating backend/.env from template..."
    cp .env.example backend/.env
fi

# Check SerpAPI key
if ! grep -q "SERPAPI_KEY=." backend/.env 2>/dev/null; then
    echo
    echo "============================================"
    echo "  SerpAPI Key - Search Global Patents"
    echo "============================================"
    echo
    echo "  Get a free API key: https://serpapi.com"
    echo
    read -p "  Paste your key (Enter to skip): " KEY
    if [ -n "$KEY" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/SERPAPI_KEY=.*/SERPAPI_KEY=$KEY/" backend/.env
        else
            sed -i "s/SERPAPI_KEY=.*/SERPAPI_KEY=$KEY/" backend/.env
        fi
        echo "  Key saved."
    fi
    echo
fi

# Install Python deps
$PYTHON -c "import fastapi" 2>/dev/null || {
    echo "[SETUP] Installing Python dependencies..."
    cd backend && pip install -q -r requirements.txt && cd "$ROOT"
}

# Build FAISS index
if [ ! -f "backend/data/faiss_index.bin" ]; then
    echo "[SETUP] Building search index..."
    cd backend && $PYTHON -m app.services.data_importer && cd "$ROOT"
fi

echo
echo "[1/2] Starting backend (first run downloads AI model)..."
$PYTHON backend/run_server.py &
BACKEND_PID=$!

echo "      Waiting for backend..."
until curl -s http://localhost:8766/api/health >/dev/null 2>&1; do sleep 3; done
echo "      Backend ready."

echo "[2/2] Starting frontend..."
cd frontend && npm run dev &
FRONTEND_PID=$!
cd "$ROOT"

echo "      Waiting for frontend..."
until curl -s http://localhost:3000 >/dev/null 2>&1; do sleep 2; done
echo "      Frontend ready."

echo
echo "============================================"
echo "  All systems ready - Opening browser"
echo "============================================"
echo

if command -v open &>/dev/null; then
    open http://localhost:3000/search
elif command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:3000/search
fi

echo "Press Enter to stop all services..."
read
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
echo "Services stopped."
