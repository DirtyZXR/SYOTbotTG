"""Скрипт для инициализации проекта"""

import subprocess
import sys
from pathlib import Path


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

    # 1. Создание виртуального окружения
    if not Path("venv").exists():
        run_command("python -m venv venv", "Создание виртуального окружения")
    else:
        print("✅ Виртуальное окружение уже существует")

    # 2. Установка зависимостей
    if Path("venv").exists():
        pip_path = (
            "venv/Scripts/pip" if sys.platform == "win32" else "venv/bin/pip"
        )
        run_command(
            f"{pip_path} install -r requirements.txt", "Установка зависимостей"
        )

    # 3. Создание структуры папок
    run_command("python setup_directories.py", "Создание структуры папок")

    # 4. Создание .env файла
    if not Path(".env").exists():
        with open(".env", "w", encoding="utf-8") as f:
            f.write(
                """BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_admin_id_here
DATABASE_PATH=./data/bot.db
DOCUMENTS_PATH=./data/documents
SECURITY_CODE=123456
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
    print("3. Запустите бота: python main.py")
    print("\n📚 Документация:")
    print("   - README.md - Общая информация")
    print("   - docs/ARCHITECTURE.md - Архитектура проекта")
    print("\n" + "=" * 50)


if __name__ == "__main__":
    init_project()
