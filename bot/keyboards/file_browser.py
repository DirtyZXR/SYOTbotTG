from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pathlib import Path
from typing import List
from config import settings


def get_folder_keyboard(
    folders_list: list, files_list: list, is_root: bool = False
) -> InlineKeyboardMarkup:
    """
    Клавиатура для навигации по папкам и файлам

    Args:
        folders_list: Список кортежей (hash, name, path) для папок
        files_list: Список кортежей (hash, name, path) для файлов
        is_root: Находимся ли мы в корневой директории
    """
    buttons = []

    # Добавляем папки
    for folder_hash, folder_name, _ in folders_list:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"📁 {folder_name}", callback_data=f"f_{folder_hash}"
                )
            ]
        )

    # Добавляем файлы
    for file_hash, file_name, _ in files_list:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"📄 {file_name}", callback_data=f"fl_{file_hash}"
                )
            ]
        )

    # Кнопка "Назад" (если не в корне)
    if not is_root:
        buttons.append(
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_folder")]
        )
    else:
        # В корне документов - кнопка "В главное меню"
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🏠 В главное меню", callback_data="back_to_menu"
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_menu_button() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    buttons = [
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
