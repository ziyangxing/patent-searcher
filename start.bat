@echo off
title Patent Searcher

echo.
echo ============================================
echo   Patent Searcher - Global Patent Search
echo ============================================
echo.

:: Check Python (try both python and python3)
set PYTHON=
python --version >nul 2>&1 && set PYTHON=python
if "%PYTHON%"=="" (
    python3 --version >nul 2>&1 && set PYTHON=python3
)
if "%PYTHON%"=="" (
    echo [ERROR] Python not found. Please install Python 3.12+
    echo         https://www.python.org/downloads/
    pause
    exit /b
)
echo Python: found
%PYTHON% --version

:: Check Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js
    echo         https://nodejs.org/
    pause
    exit /b
)
echo Node: found

:: Frontend deps
if not exist "frontend\node_modules\" (
    echo.
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
    echo Done.
)

:: Config file
if not exist "backend\.env" (
    echo.
    echo Creating config from template...
    copy .env.example backend\.env >nul
    echo.
    echo ============================================
    echo   Enter your SerpAPI key (free)
    echo   Get one at: https://serpapi.com
    echo ============================================
    set /p KEY="Key (Enter to skip): "
    powershell -NoProfile -Command "(Get-Content 'backend\.env') -replace 'SERPAPI_KEY=.+', 'SERPAPI_KEY=!KEY!' | Set-Content 'backend\.env'"
)

:: Python deps
%PYTHON% -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Installing Python dependencies...
    cd backend
    pip install -q -r requirements.txt
    cd ..
    echo Done.
)

:: FAISS index
if not exist "backend\data\faiss_index.bin" (
    echo.
    echo Building search index...
    cd backend
    %PYTHON% -m app.services.data_importer
    cd ..
    echo Done.
)

echo.
echo ============================================
echo   Starting backend server...
echo   (First run downloads AI model ~80MB)
echo ============================================
start "Backend" cmd /c "cd /d %cd%\backend && %PYTHON% run_server.py"

echo Waiting for backend to be ready...
:wait_backend
timeout /t 3 /nobreak >nul
curl -s http://localhost:8766/api/health >nul 2>&1
if %errorlevel% neq 0 goto wait_backend
echo Backend: READY

echo.
echo Starting frontend...
start "Frontend" cmd /c "cd /d %cd%\frontend && npm run dev"

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
