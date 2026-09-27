@echo off
title Manim Render Studio - Local Launcher
color 0A

echo =======================================================================
echo               🎬 MANIM RENDER STUDIO - LOCAL LAUNCHER
echo =======================================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if errorlevel 1 goto NO_PYTHON

echo [*] Found Python installation.

:: 2. Check Virtual Environment
if exist venv\Scripts\activate.bat goto ACTIVATE_VENV

echo [INFO] Creating Python virtual environment (venv)...
python -m venv venv
if errorlevel 1 goto VENV_ERROR
echo [*] Virtual environment created successfully.

:ACTIVATE_VENV
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: 3. Check dependencies
python -c "import manim" >nul 2>&1
if errorlevel 1 goto INSTALL_DEPS
echo [*] All required packages are ready!
goto LAUNCH_APP

:INSTALL_DEPS
echo.
echo [INFO] First-time setup: Installing Manim dependencies...
echo [INFO] This takes 1-2 minutes on first run, please wait...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if errorlevel 1 goto PIP_ERROR
echo [*] Installation complete!

:LAUNCH_APP
echo.
echo =======================================================================
echo  🚀 SERVER IS RUNNING AT: http://localhost:7860
echo.
echo  ⚠️  IMPORTANT: DO NOT CLOSE THIS BLACK CMD TERMINAL WINDOW!
echo     The server runs inside this window. Closing it stops the server.
echo =======================================================================
echo.

start "" "http://localhost:7860"

python app.py
goto END

:NO_PYTHON
echo [ERROR] Python is not installed or not on your system PATH!
echo Please install Python 3.10 or 3.11 from https://www.python.org/
echo Check "Add Python to PATH" during installation.
pause
exit /b 1

:VENV_ERROR
echo [ERROR] Failed to create virtual environment.
pause
exit /b 1

:PIP_ERROR
echo [WARNING] Dependency installation had errors, attempting to continue...
goto LAUNCH_APP

:END
pause
