from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional
from config import DOCUMENT_CATEGORIES


def get_categories_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с категориями документов"""
    buttons = []
    for key, data in DOCUMENT_CATEGORIES.items():
        buttons.append(
            [
                InlineKeyboardButton(
                    text=data["name"],
                    callback_data=f"category_{key}",
                )
            ]
        )

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_subcategories_keyboard(category: str) -> InlineKeyboardMarkup:
    """Клавиатура с подкатегориями"""
    buttons = []

    if category not in DOCUMENT_CATEGORIES:
        return InlineKeyboardMarkup(inline_keyboard=[])

    category_data = DOCUMENT_CATEGORIES[category]
    subcategories = category_data.get("subcategories", [])

    # Обработка вложенных подкатегорий
    if isinstance(subcategories, dict):
        for key, data in subcategories.items():
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=data["name"],
                        callback_data=f"subcategory_{category}_{key}",
                    )
                ]
            )
    else:
        for subcategory in subcategories:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=subcategory,
                        callback_data=f"subcategory_{category}_{subcategory}",
                    )
                ]
            )

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_documents_keyboard(documents: List) -> InlineKeyboardMarkup:
    """Клавиатура со списком документов"""
    buttons = []

    for doc in documents:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=doc.name,
                    callback_data=f"document_{doc.id}",
                )
            ]
        )

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_test_groups_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с группами тестов"""
    buttons = [
        [InlineKeyboardButton(text="Группа 2", callback_data="test_group_2")],
        [InlineKeyboardButton(text="Группа 3", callback_data="test_group_3")],
        [InlineKeyboardButton(text="Группа 4", callback_data="test_group_4")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_test_answers_keyboard(question_num: int, options: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура с вариантами ответов на вопрос теста"""
    buttons = []

    for idx, option in enumerate(options, 1):
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{idx}. {option}",
                    callback_data=f"answer_{question_num}_{idx}",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    buttons = [
        [InlineKeyboardButton(text="📚 Документы", callback_data="menu_documents")],
        [InlineKeyboardButton(text="📝 Тесты", callback_data="menu_tests")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    buttons = [
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_registration")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)
