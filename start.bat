@echo off
chcp 65001 >nul
title Patent Searcher

echo ============================================
echo      Patent Searcher - 智能专利检索工具
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.12+
    pause
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js 22+
    pause
    exit /b 1
)

:: Check frontend dependencies
if not exist "frontend\node_modules" (
    echo [WARN] Frontend dependencies not installed. Running npm install...
    cd frontend
    call npm install
    cd ..
)

echo [1/2] Starting backend server...
start "PatentSearcher-Backend" cmd /c "cd backend && python run_server.py"

:: Wait for backend
echo         Waiting for backend to be ready...
:wait_backend
timeout /t 2 /nobreak >nul
curl -s http://localhost:8766/api/health >nul 2>&1
if %errorlevel% neq 0 (
    goto wait_backend
)
echo         Backend ready!

echo [2/2] Starting frontend...
start "PatentSearcher-Frontend" cmd /c "cd frontend && echo NEXT_PUBLIC_API_URL=http://localhost:8766/api > .env.local && npm run dev"

:: Wait for frontend
echo         Waiting for frontend to be ready...
:wait_frontend
timeout /t 2 /nobreak >nul
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% neq 0 (
    goto wait_frontend
)

echo.
echo ============================================
echo      All systems ready!
echo      Opening browser...
echo ============================================
start http://localhost:3000/search

echo.
echo Press any key to stop all services...
pause >nul
taskkill /FI "WINDOWTITLE eq PatentSearcher-*" /F >nul 2>&1
echo Services stopped.
