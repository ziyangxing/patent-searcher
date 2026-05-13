#!/bin/bash

echo "============================================"
echo "     Patent Searcher - 智能专利检索工具"
echo "============================================"
echo

# Check Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[ERROR] Python not found. Please install Python 3.12+"
    exit 1
fi
PYTHON=$(command -v python3 || command -v python)

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js not found. Please install Node.js 22+"
    exit 1
fi

# Check frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo "[WARN] Frontend dependencies not installed. Running npm install..."
    cd frontend && npm install && cd ..
fi

ROOT_DIR=$(pwd)

# Start backend
echo "[1/2] Starting backend server..."
$PYTHON backend/run_server.py &
BACKEND_PID=$!

# Wait for backend
echo "      Waiting for backend..."
until curl -s http://localhost:8766/api/health > /dev/null 2>&1; do
    sleep 2
done
echo "      Backend ready!"

# Start frontend
echo "[2/2] Starting frontend..."
cd frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8766/api" > .env.local
npm run dev &
FRONTEND_PID=$!
cd "$ROOT_DIR"

# Wait for frontend
echo "      Waiting for frontend..."
until curl -s http://localhost:3000 > /dev/null 2>&1; do
    sleep 2
done

echo
echo "============================================"
echo "     All systems ready!"
echo "     Opening browser..."
echo "============================================"

# Open browser
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
