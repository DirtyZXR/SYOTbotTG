"""Скрипт для создания структуры папок документов"""

import os
from pathlib import Path


def create_directory_structure():
    """Создаёт структуру папок для документов"""

    base_path = Path("data/documents")

    structure = {
        "гоичс": ["Инструкции", "Лекции"],
        "охрана_труда": [
            "Инструкции",
            "Нормативная документация",
            "Положения",
            "Программа обучения",
        ],
        "электробезопасность": {
            "админ_тех_перс": ["Билеты", "Тесты"],
            "неэлектр_перс": ["Общие документы"],
            "нормативка": ["Инструкции", "Первая помощь", "ПУЭ"],
        },
        "пожар_безопасность": ["Документы", "Материалы"],
    }

    # Создаём базовую папку
    base_path.mkdir(parents=True, exist_ok=True)

    # Создаём структуру папок
    for category, subcategories in structure.items():
        category_path = base_path / category

        if isinstance(subcategories, dict):
            # Вложенные подкатегории
            for sub_key, sub_items in subcategories.items():
                sub_path = category_path / sub_key
                sub_path.mkdir(parents=True, exist_ok=True)

                for item in sub_items:
                    item_path = sub_path / item
                    item_path.mkdir(parents=True, exist_ok=True)
        else:
            # Простые подкатегории
            for subcategory in subcategories:
                sub_path = category_path / subcategory
                sub_path.mkdir(parents=True, exist_ok=True)

    # Создаём папку для тестов
    tests_path = Path("data/tests")
    tests_path.mkdir(parents=True, exist_ok=True)

    # Создаём папку для базы данных
    db_path = Path("data")
    db_path.mkdir(parents=True, exist_ok=True)

    print("✅ Структура папок создана успешно!")
    print(f"📁 Базовая папка: {base_path.absolute()}")
    print(f"📁 Папка тестов: {tests_path.absolute()}")


if __name__ == "__main__":
    create_directory_structure()
