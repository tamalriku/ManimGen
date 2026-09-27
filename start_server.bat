@echo off
title Manim Render Studio - Fast Launcher
call venv\Scripts\activate.bat
start "" "http://localhost:7860"
python app.py
pause
