from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_leaderboard_keyboard(
    current_group: int, total_pages: int, current_page: int
) -> InlineKeyboardMarkup:
    """Клавиатура для таблицы лидеров с пагинацией и выбором группы"""
    buttons = []

    # Кнопки переключения групп
    other_group = 3 if current_group == 2 else 2
    buttons.append(
        [
            InlineKeyboardButton(
                text=f"Переключить на {'III' if other_group == 3 else 'II'} группу",
                callback_data=f"leaderboard_group_{other_group}_0",
            )
        ]
    )

    # Пагинация
    pagination_row = []
    if current_page > 0:
        pagination_row.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"leaderboard_group_{current_group}_{current_page - 1}",
            )
        )
    if current_page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"leaderboard_group_{current_group}_{current_page + 1}",
            )
        )

    if pagination_row:
        buttons.append(pagination_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)
