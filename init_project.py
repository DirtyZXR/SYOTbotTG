"""Скрипт для инициализации проекта"""

import subprocess
import sys
from pathlib import Path

PYTHON_VERSION = "3.12"


def run_command(cmd: str, description: str):
    """Выполняет команду с выводом"""
    print(f"\n🔧 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Ошибка: {result.stderr}")
        return False

    print(f"✅ {description} завершено")
    return True


def init_project():
    """Инициализация проекта"""

    print("🚀 Инициализация проекта SYOTbotTG\n")

    python_cmd = (
        f"py -{PYTHON_VERSION}"
        if sys.platform == "win32"
        else f"python{PYTHON_VERSION}"
    )

    # 1. Создание виртуального окружения
    if not Path("venv").exists():
        run_command(
            f"{python_cmd} -m venv venv",
            f"Создание виртуального окружения на Python {PYTHON_VERSION}",
        )
    else:
        print("✅ Виртуальное окружение уже существует")

    # 2. Установка зависимостей
    if Path("venv").exists():
        # Используем абсолютный путь для надежности
        venv_path = Path("venv").resolve()
        pip_path = (
            venv_path / "Scripts" / "pip"
            if sys.platform == "win32"
            else venv_path / "bin" / "pip"
        )
        run_command(
            f'"{pip_path}" install -r requirements.txt', "Установка зависимостей"
        )

    # 4. Создание .env файла
    if not Path(".env").exists():
        with open(".env", "w", encoding="utf-8") as f:
            f.write(
                """BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_admin_id_here
DATABASE_PATH=./data/bot.db
DOCUMENTS_PATH=./data/documents
"""
            )
        print("✅ Файл .env создан")
    else:
        print("✅ Файл .env уже существует")

    print("\n" + "=" * 50)
    print("🎉 Инициализация завершена!")
    print("=" * 50)
    print("\n📋 Следующие шаги:")
    print("1. Отредактируйте файл .env:")
    print("   - BOT_TOKEN: Получите у @BotFather")
    print("   - ADMIN_ID: Ваш Telegram ID (узнать у @userinfobot)")
    print("   - SECURITY_CODE: Код для верификации пользователей")
    print("\n2. Добавьте документы в папку data/documents/")
    print("3. Запустите бота: venv\\Scripts\\python.exe main.py")
    print("\n📚 Документация:")
    print("   - README.md - Общая информация")
    print("\n" + "=" * 50)


if __name__ == "__main__":
    init_project()
