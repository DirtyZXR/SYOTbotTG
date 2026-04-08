from typing import Optional
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from core.auth_service import AuthService
from models.user import User


def get_main_menu_keyboard(user_id: Optional[int] = None) -> ReplyKeyboardMarkup:
    """Главное меню (Reply)"""
    is_intellectika = False
    is_admin = False

    if user_id:
        user = AuthService.get_user(user_id)
        if user:
            if "intellectika" in (user.companies or []):
                is_intellectika = True
            if user.is_admin:
                is_admin = True

    # Строим ряды кнопок
    keyboard = []

    # 1 ряд - Документы (доступны всем)
    keyboard.append([KeyboardButton(text="📚 Документы")])

    # 2 ряд - Тесты (только для Интеллектики) и Рейтинг (для Интеллектики и админов)
    row_2 = []
    if is_intellectika:
        row_2.append(KeyboardButton(text="📝 Тесты"))

    if is_intellectika or is_admin:
        row_2.append(KeyboardButton(text="🏆 Рейтинг"))

    if row_2:
        keyboard.append(row_2)

    # 3 ряд - Статистика и Профиль (доступны всем)
    keyboard.append(
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="✏️ Мои данные")]
    )

    # 4 ряд - Админ-панель (только для админов)
    if is_admin:
        keyboard.append([KeyboardButton(text="🔧 Админ-панель")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True,  # Клавиатура будет видна всегда
    )


def get_profile_keyboard() -> ReplyKeyboardMarkup:
    """Меню профиля (Reply)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✏️ Изменить ФИО"),
                KeyboardButton(text="📧 Изменить email"),
            ],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def get_test_groups_keyboard(user: User) -> ReplyKeyboardMarkup:
    """Меню выбора тестов (Reply)"""
    from core.test_service import is_group_available

    keyboard = []

    # Группа 2
    if is_group_available(user, 2):
        keyboard.append([KeyboardButton(text="📋 II группа до 1000В")])

    # Группа 3
    if is_group_available(user, 3):
        keyboard.append([KeyboardButton(text="📋 III группа до 1000В")])

    # Кнопка назад
    keyboard.append([KeyboardButton(text="🔙 Назад")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены для FSM (Reply)"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
        is_persistent=True,
    )
