@echo off
title Patent Searcher

:: Change to the script's directory (fixes "System32" issue)
cd /d "%~dp0"

echo.
echo ============================================
echo   Patent Searcher - Global Patent Search
echo ============================================
echo.

:: Check Python
set PYTHON=
python --version >nul 2>&1 && set PYTHON=python
if "%PYTHON%"=="" (
    python3 --version >nul 2>&1 && set PYTHON=python3
)
if "%PYTHON%"=="" (
    echo [ERROR] Python not found. Install Python 3.12+
    echo         https://www.python.org/downloads/
    pause
    exit /b
)
echo Python: found

:: Check Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found.
    echo         https://nodejs.org/
    pause
    exit /b
)
echo Node: found

:: Frontend deps
if not exist "%~dp0frontend\node_modules\" (
    echo.
    echo Installing frontend dependencies...
    cd /d "%~dp0frontend"
    call npm install
    cd /d "%~dp0"
    echo Done.
)

:: Config file
if not exist "%~dp0backend\.env" (
    echo.
    echo Creating config from template...
    copy "%~dp0.env.example" "%~dp0backend\.env" >nul
    echo.
    echo ============================================
    echo   Enter your SerpAPI key (free)
    echo   Get one at: https://serpapi.com
    echo ============================================
    set /p KEY="Key (Enter to skip): "
    powershell -NoProfile -Command "(Get-Content '%~dp0backend\.env') -replace 'SERPAPI_KEY=.+', 'SERPAPI_KEY=!KEY!' | Set-Content '%~dp0backend\.env'"
)

:: Python deps
%PYTHON% -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Installing Python dependencies...
    cd /d "%~dp0backend"
    pip install -q -r requirements.txt
    cd /d "%~dp0"
    echo Done.
)

:: FAISS index
if not exist "%~dp0backend\data\faiss_index.bin" (
    echo.
    echo Building search index...
    cd /d "%~dp0backend"
    %PYTHON% -m app.services.data_importer
    cd /d "%~dp0"
    echo Done.
)

echo.
echo ============================================
echo   Starting backend server...
echo   (First run downloads AI model ~80MB)
echo ============================================
start "Backend" cmd /c "cd /d %~dp0backend && %PYTHON% run_server.py"

echo Waiting for backend to be ready...
:wait_backend
timeout /t 3 /nobreak >nul
curl -s http://localhost:8766/api/health >nul 2>&1
if %errorlevel% neq 0 goto wait_backend
echo Backend: READY

echo.
echo Starting frontend...
start "Frontend" cmd /c "cd /d %~dp0frontend && npm run dev"

echo Waiting for frontend to be ready...
:wait_frontend
timeout /t 2 /nobreak >nul
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% neq 0 goto wait_frontend
echo Frontend: READY

echo.
echo ============================================
echo   Opening browser...
echo ============================================
start http://localhost:3000/search

echo.
echo Patent Searcher is running!
echo Close this window to stop all services.
pause >nul

taskkill /FI "WINDOWTITLE eq Backend" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend" /F >nul 2>&1
