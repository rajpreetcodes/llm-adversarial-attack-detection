@echo off
title DGAD Project Launcher
echo ===================================================
echo   DGAD (Disagreement-Gated Adaptive Detection)
echo             System Launcher
echo ===================================================
echo.

set SCRIPT_DIR=%~dp0
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    cd /d "%SCRIPT_DIR%"
) else if exist "%SCRIPT_DIR%main\.venv\Scripts\python.exe" (
    cd /d "%SCRIPT_DIR%main"
) else (
    echo [ERROR] Virtual environment .venv not found.
    echo Please make sure you run this script from the project folder.
    pause
    exit /b 1
)

echo [1/3] Launching FastAPI Backend Server (Port 8000)...
start "DGAD API Backend" cmd /k "title DGAD API Backend && .venv\Scripts\python.exe -m uvicorn dgad.api.main:app --port 8000"

echo [2/3] Launching Dashboard Development Server (Port 5173)...
start "DGAD Dashboard" cmd /k "title DGAD Dashboard && cd dashboard && npm run dev"

echo [3/3] Waiting 4 seconds for servers to start...
ping -n 5 127.0.0.1 >nul

echo Opening Dashboard in your default web browser...
start http://localhost:5173/

echo.
echo ===================================================
echo   Services are running!
echo   - Dashboard: http://localhost:5173/
echo   - API Docs:  http://localhost:8000/docs
echo   - Health:    http://localhost:8000/health
echo ===================================================
echo.
pause
