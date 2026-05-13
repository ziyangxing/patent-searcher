@echo off
chcp 65001 >nul
title Patent Searcher

echo ============================================
echo      Patent Searcher - AI Patent Search
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.12+ is required but not found.
    echo         Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js 22+ is required but not found.
    echo         Download: https://nodejs.org/
    pause
    exit /b 1
)

:: Install frontend deps if needed
if not exist "frontend\node_modules" (
    echo [SETUP] Installing frontend dependencies (first time only)...
    cd frontend
    call npm install
    cd ..
    echo [SETUP] Done.
    echo.
)

:: Check SerpAPI key
findstr /C:"SERPAPI_KEY=" backend\.env > temp_key_check.txt 2>nul
set HAS_KEY=0
for /f "tokens=2 delims==" %%a in (temp_key_check.txt) do (
    if not "%%a"=="" set HAS_KEY=1
)
del temp_key_check.txt 2>nul

if %HAS_KEY%==0 (
    echo.
    echo ============================================
    echo   IMPORTANT: SerpAPI Key Required
    echo ============================================
    echo.
    echo   To search global patents, you need a free API key:
    echo.
    echo   1. Open https://serpapi.com in your browser
    echo   2. Click "Get Free API Key" and sign up (30s)
    echo   3. Copy your key
    echo.
    set /p USER_KEY="   Paste your SerpAPI key here (or press Enter to skip): "
    if not "!USER_KEY!"=="" (
        powershell -Command "(Get-Content backend\.env) -replace 'SERPAPI_KEY=.*', 'SERPAPI_KEY=!USER_KEY!' | Set-Content backend\.env"
        echo   Key saved!
    ) else (
        echo   Skipped. Will use local search mode only.
    )
    echo.
)

:: Install Python deps if needed
python -c "import fastapi" 2>nul
if %errorlevel% neq 0 (
    echo [SETUP] Installing Python dependencies (first time only)...
    cd backend
    pip install -r requirements.txt
    cd ..
    echo [SETUP] Done.
    echo.
)

:: Build FAISS index if needed
if not exist "backend\data\faiss_index.bin" (
    echo [SETUP] Building patent index (first time only)...
    cd backend
    python -m app.services.data_importer
    cd ..
    echo.
)

echo [1/2] Starting backend server (loading AI model, ~20s first time)...
start "PatentSearcher-Backend" cmd /c "cd backend && python run_server.py"

echo         Waiting for backend...
:wait_backend
timeout /t 3 /nobreak >nul
curl -s http://localhost:8766/api/health >nul 2>&1
if %errorlevel% neq 0 goto wait_backend
echo         Backend ready!

echo [2/2] Starting frontend...
start "PatentSearcher-Frontend" cmd /c "cd frontend && npm run dev"

echo         Waiting for frontend...
:wait_frontend
timeout /t 2 /nobreak >nul
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% neq 0 goto wait_frontend
echo         Frontend ready!

echo.
echo ============================================
echo      All systems ready!
echo      Opening browser...
echo ============================================
start http://localhost:3000/search

echo.
echo Close this window to stop all services.
pause >nul
taskkill /FI "WINDOWTITLE eq PatentSearcher-*" /F >nul 2>&1
echo Services stopped.
