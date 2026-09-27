@echo off
setlocal enabledelayedexpansion
title Manim Render Studio - Local Server Launcher
color 0A

echo =======================================================================
echo               🎬 MANIM RENDER STUDIO - LOCAL LAUNCHER
echo =======================================================================
echo.
echo  This script will start your local Manim rendering server on Windows.
echo  No GPU quotas, no cloud limits, 100%% private & unlimited local rendering!
echo =======================================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not on your system PATH!
    echo Please install Python 3.10 or 3.11 from https://www.python.org/
    echo [CRITICAL] Be sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VER=%%i
echo [✓] Found %PYTHON_VER%

:: 2. Create Virtual Environment
if not exist "venv\Scripts\activate.bat" (
    echo.
    echo [INFO] First time setup detected. Creating Python virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment. Please check your Python installation.
        pause
        exit /b 1
    )
    echo [✓] Virtual environment created successfully.
)

:: 3. Activate Virtual Environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: 4. Install Dependencies
echo [INFO] Checking & installing dependencies (Manim, Gradio, FFmpeg, PIL)...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Dependency check completed with warnings. Attempting to launch...
)

:: 5. Open Web Browser
echo.
echo =======================================================================
echo  🚀 STARTING LOCAL STUDIO AT: http://localhost:7860
echo  Press Ctrl+C in this terminal window anytime to stop the server.
echo =======================================================================
echo.

start "" "http://localhost:7860"

:: 6. Launch Application
python app.py

pause
