@echo off
chcp 65001 >nul
echo ========================================
echo Сборка SYOTbotTG в EXE файл
echo ========================================
echo.

REM Проверяем наличие виртуального окружения
if not exist "venv\Scripts\activate.bat" (
    echo [ОШИБКА] Виртуальное окружение не найдено!
    echo Сначала создайте виртуальное окружение:
    echo   py -3.12 -m venv venv
    echo   venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

REM Активируем виртуальное окружение
call venv\Scripts\activate.bat

REM Проверяем наличие .env файла
if not exist ".env" (
    echo [ВНИМАНИЕ] Файл .env не найден!
    echo Создайте его на основе .env.example и заполните настройки.
    echo.
    set /p continue="Продолжить сборку? (y/n): "
    if /i not "%continue%"=="y" (
        echo Сборка отменена.
        pause
        exit /b 1
    )
)

REM Устанавливаем зависимости
echo.
echo [1/3] Установка зависимостей...
pip install -r requirements.txt --upgrade
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить зависимости.
    pause
    exit /b 1
)

REM Создаём папку для логов
if not exist "logs" mkdir logs

REM Собираем EXE файл
echo.
echo [2/3] Сборка EXE файла...
pyinstaller --clean syotbot.spec
if errorlevel 1 (
    echo [ОШИБКА] Не удалось собрать EXE файл.
    pause
    exit /b 1
)

REM Копируем .env файл в папку с EXE
echo.
echo [3/3] Копирование файлов...
if exist ".env" (
    copy ".env" "dist\.env" >nul
    echo [OK] .env скопирован
)

REM Копируем папку data если она существует
if exist "data" (
    xcopy /E /I /Y "data" "dist\data" >nul
    echo [OK] Папка data скопирована
)

echo.
echo ========================================
echo Сборка завершена успешно!
echo ========================================
echo.
echo EXE файл находится в папке: dist\SYOTbotTG.exe
echo.
echo Для запуска на другом ПК скопируйте:
echo   - dist\SYOTbotTG.exe
echo   - dist\.env (настройте его на новом ПК)
echo   - dist\data\ (папка с документами и тестами)
echo.
pause
