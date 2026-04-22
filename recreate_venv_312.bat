@echo off
setlocal

echo ===============================================
echo Recreating virtual environment for Python 3.12
echo ===============================================

where py >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python launcher ^("py"^) not found.
    pause
    exit /b 1
)

py -3.12 --version >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python 3.12 is not installed or unavailable via py -3.12.
    pause
    exit /b 1
)

if exist "venv" (
    echo [INFO] Existing "venv" folder found.
    ren venv venv_py314_backup
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to rename old virtual environment.
        pause
        exit /b 1
    )
)

echo [1/4] Creating venv with Python 3.12...
py -3.12 -m venv venv
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b %ERRORLEVEL%
)

echo [2/4] Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to upgrade pip.
    pause
    exit /b %ERRORLEVEL%
)

echo [3/4] Installing requirements...
venv\Scripts\python.exe -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b %ERRORLEVEL%
)

echo [4/4] Updating database schema...
venv\Scripts\python.exe -m pip install alembic
venv\Scripts\python.exe -m alembic upgrade head
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to apply migrations.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ===============================================
echo Python 3.12 environment is ready.
echo Start the bot with: venv\Scripts\python.exe main.py
echo ===============================================
pause
