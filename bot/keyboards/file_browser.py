from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pathlib import Path
from typing import List
from config import settings


def get_folder_keyboard(folder_path: str, relative_path: str = "") -> InlineKeyboardMarkup:
    """
    Клавиатура для навигации по папкам и файлам

    Args:
        folder_path: Полный путь к папке
        relative_path: Относительный путь от data/documents (для навигации)
    """
    folder = Path(folder_path)

    if not folder.exists() or not folder.is_dir():
        return InlineKeyboardMarkup(inline_keyboard=[])

    buttons = []
    items = sorted(folder.iterdir(), key=lambda x: (not x.is_dir(), x.name))

    # Сначала папки, потом файлы
    folders = [item for item in items if item.is_dir()]
    files = [item for item in items if item.is_file()]

    # Добавляем папки (используем хеш имени для короткого callback_data)
    import hashlib
    for folder_item in folders:
        # Создаем короткий хеш для callback_data (максимум 64 байта)
        name_hash = hashlib.md5(folder_item.name.encode('utf-8')).hexdigest()[:8]
        buttons.append([
            InlineKeyboardButton(
                text=f"📁 {folder_item.name}",
                callback_data=f"f_{name_hash}"
            )
        ])

    # Добавляем файлы (используем хеш имени)
    for file_item in files:
        name_hash = hashlib.md5(file_item.name.encode('utf-8')).hexdigest()[:8]
        buttons.append([
            InlineKeyboardButton(
                text=f"📄 {file_item.name}",
                callback_data=f"fl_{name_hash}"
            )
        ])

    # Кнопка "Назад" (если не в корне)
    if relative_path:
        buttons.append([
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_folder"
            )
        ])
    else:
        # В корне документов - кнопка "В главное меню"
        buttons.append([
            InlineKeyboardButton(
                text="🏠 В главное меню",
                callback_data="back_to_menu"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_menu_button() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    buttons = [[InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
