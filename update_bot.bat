@echo off
echo ===================================================
echo Starting SYOTbotTG update...
echo ===================================================

echo.
echo [1/4] Pulling new files from repository (git pull)...
git pull
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Git pull failed. Check internet connection or merge conflicts.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/4] Checking virtual environment...
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment "venv" not found in the current folder!
    pause
    exit /b 1
)

echo.
echo [3/4] Installing and updating dependencies...
venv\Scripts\python.exe -m ensurepip --default-pip
venv\Scripts\python.exe -m pip install --upgrade pip

if exist "requirements.txt" (
    venv\Scripts\python.exe -m pip install -r requirements.txt
) else (
    echo [WARNING] requirements.txt not found. Skipping.
)
venv\Scripts\python.exe -m pip install alembic

echo.
echo [4/4] Updating database structure...
venv\Scripts\python.exe -m alembic upgrade head
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to update the database ^(Alembic migrations^).
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ===================================================
echo Update completed successfully! 
echo The database is up to date.
echo You can now start the bot normally.
echo ===================================================
pause