@echo off
setlocal enabledelayedexpansion
title Manim Render Studio - Local Server Launcher
color 0A

echo =======================================================================
echo               🎬 MANIM RENDER STUDIO - LOCAL LAUNCHER
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
echo [✓] %PYTHON_VER%

:: 2. Create Virtual Environment if missing
if not exist "venv\Scripts\activate.bat" (
    echo.
    echo [INFO] Creating Python virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [✓] Virtual environment created.
)

:: 3. Activate Virtual Environment
call venv\Scripts\activate.bat

:: 4. Quick check if manim is installed
python -c "import manim" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [INFO] First-time setup: Installing Manim dependencies...
    echo (This takes 1-2 minutes on first run, please wait...)
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt
    echo [✓] Installation complete!
) else (
    echo [✓] All required packages are ready!
)

:: 5. Open Web Browser and Start Server
echo.
echo =======================================================================
echo  🚀 STARTING SERVER AT: http://localhost:7860
echo  Keep this window open while using the Studio.
echo =======================================================================
echo.

start "" "http://localhost:7860"

python app.py

pause
