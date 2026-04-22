@echo off
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment "venv" not found.
    echo Run recreate_venv_312.bat first.
    pause
    exit /b 1
)

venv\Scripts\python.exe main.py
