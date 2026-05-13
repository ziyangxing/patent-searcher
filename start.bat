@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Patent Searcher

echo.
echo ============================================
echo   Patent Searcher - AI Global Patent Search
echo ============================================
echo.

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.12+
    echo         https://www.python.org/downloads/
    pause
    exit /b
)

:: Check Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install Node.js
    echo         https://nodejs.org/
    pause
    exit /b
)

:: Install frontend deps
if not exist "frontend\node_modules" (
    echo [SETUP] Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

:: Check if .env exists, copy from example if not
if not exist "backend\.env" (
    echo [SETUP] Creating backend/.env from template...
    copy .env.example backend\.env >nul
)

:: Check SerpAPI key
set KEY=
for /f "tokens=2 delims==" %%a in ('findstr "SERPAPI_KEY" backend\.env 2^>nul') do set KEY=%%a
if "!KEY!"=="" (
    echo.
    echo ============================================
    echo   SerpAPI Key - Search Global Patents
    echo ============================================
    echo.
    echo   Get a free API key (30 seconds):
    echo   1. Open https://serpapi.com
    echo   2. Sign up -^> Get Free API Key -^> Copy
    echo.
    set /p NEWKEY="   Paste your key (Enter to skip): "
    if not "!NEWKEY!"=="" (
        powershell -NoProfile -Command "(Get-Content backend\.env) -replace 'SERPAPI_KEY=.*', 'SERPAPI_KEY=!NEWKEY!' | Set-Content backend\.env -Encoding UTF8"
        echo   Key saved.
    )
)

:: Install Python deps
python -c "import fastapi" 2>nul
if %errorlevel% neq 0 (
    echo [SETUP] Installing Python dependencies...
    cd backend
    pip install -q -r requirements.txt
    cd ..
)

:: Build FAISS index
if not exist "backend\data\faiss_index.bin" (
    echo [SETUP] Building search index...
    cd backend
    python -m app.services.data_importer
    cd ..
)

echo.
echo [1/2] Starting backend (first run downloads AI model ~80MB)...
start "PatentSearcher-Backend" /min cmd /c "cd /d %cd%\backend && python run_server.py && pause"

echo         Waiting for backend to be ready...
:wait_backend
timeout /t 3 /nobreak >nul
curl -s http://localhost:8766/api/health >nul 2>&1
if %errorlevel% neq 0 goto wait_backend
echo         Backend ready.

echo [2/2] Starting frontend...
start "PatentSearcher-Frontend" /min cmd /c "cd /d %cd%\frontend && npm run dev"

echo         Waiting for frontend...
:wait_frontend
timeout /t 2 /nobreak >nul
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% neq 0 goto wait_frontend
echo         Frontend ready.

echo.
echo ============================================
echo   All systems ready - Opening browser
echo ============================================
echo.
start http://localhost:3000/search

echo Close this window to stop all services.
pause >nul

taskkill /FI "WINDOWTITLE eq PatentSearcher-*" /F >nul 2>&1
