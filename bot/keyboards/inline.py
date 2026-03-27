from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional
from config import DOCUMENT_CATEGORIES
from core import AuthService


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


def get_main_menu_keyboard(user_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Главное меню"""
    buttons = [
        [InlineKeyboardButton(text="📚 Документы", callback_data="menu_documents")],
        [InlineKeyboardButton(text="📝 Тесты", callback_data="menu_tests")],
    ]

    # Добавляем кнопку админ-панели только для администраторов
    if user_id and AuthService.is_admin(user_id):
        buttons.append([InlineKeyboardButton(text="🔧 Админ-панель", callback_data="menu_admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    buttons = [
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_registration")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура админского меню"""
    buttons = [
        [InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_users")],
        [InlineKeyboardButton(text="👨‍💼 Управление админами", callback_data="admin_manage_admins")],
        [InlineKeyboardButton(text="🔑 Сменить секретный код", callback_data="admin_change_code")],
        [InlineKeyboardButton(text="📝 Сканировать тесты", callback_data="admin_load_tests")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_menu")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_manage_admins_keyboard(users) -> InlineKeyboardMarkup:
    """Клавиатура для управления админами"""
    buttons = []

    for user in users:
        # Показываем только верифицированных пользователей
        if user.is_verified:
            status = "👨‍💼" if user.is_admin else "👤"
            action = "remove_admin" if user.is_admin else "add_admin"
            button_text = f"{status} {user.full_name or user.email}"

            buttons.append([
                InlineKeyboardButton(text=button_text, callback_data=f"{action}_{user.id}")
            ])

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin_menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_operation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены операции"""
    buttons = [
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_operation")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)
