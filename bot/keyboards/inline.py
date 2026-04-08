from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional
from config import DOCUMENT_CATEGORIES, settings
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

    buttons.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    )

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

    buttons.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    )

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

    buttons.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_test_answers_keyboard(
    question_num: int, options: List[str]
) -> InlineKeyboardMarkup:
    """Клавиатура с вариантами ответов (только номера)"""
    buttons = []
    row = []
    for idx, option in enumerate(options):
        row.append(
            InlineKeyboardButton(
                text=str(idx + 1), callback_data=f"answer_{question_num}_{idx + 1}"
            )
        )
    buttons.append(row)
    # Добавляем кнопку отмены теста отдельной строкой
    buttons.append(
        [InlineKeyboardButton(text="❌ Прервать тест", callback_data="test_cancel")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    buttons = [
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_registration")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_approval_keyboard(pending_user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения регистрации пользователя"""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=f"admin_approve_{pending_user_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"admin_reject_{pending_user_id}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура админского меню"""
    buttons = [
        [
            InlineKeyboardButton(
                text="👥 Все пользователи", callback_data="admin_list_users_1"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔍 Поиск пользователей", callback_data="admin_search_users"
            )
        ],
        # [
        #     InlineKeyboardButton(
        #         text="👨‍💼 Управление админами", callback_data="admin_manage_admins"
        #     )
        # ],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_menu")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_manage_admins_keyboard(users) -> InlineKeyboardMarkup:
    """Клавиатура для управления админами"""
    buttons = []

    for user in users:
        # Показываем только верифицированных пользователей
        if not user.is_pending:
            status = "👨‍💼" if user.is_admin else "👤"
            action = "remove_admin" if user.is_admin else "add_admin"
            button_text = f"{status} {user.full_name or user.email}"

            buttons.append(
                [
                    InlineKeyboardButton(
                        text=button_text, callback_data=f"{action}_{user.id}"
                    )
                ]
            )

    buttons.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin_menu")]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_operation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены операции"""
    buttons = [
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_operation")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_user_search_results_keyboard(users) -> InlineKeyboardMarkup:
    """Клавиатура с результатами поиска пользователей"""
    buttons = []

    for user in users:
        status = "👨‍💼" if user.is_admin else ("✅" if user.is_verified else "⏳")
        display = user.full_name or user.email
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{status} {display}",
                    callback_data=f"admin_user_{user.id}",
                )
            ]
        )

    buttons.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin_menu")]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_user_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий администратора над пользователем"""
    buttons = [
        [
            InlineKeyboardButton(
                text="✏️ Изменить ФИО", callback_data=f"admin_edit_name_{user_id}"
            ),
            InlineKeyboardButton(
                text="📧 Изменить email", callback_data=f"admin_edit_email_{user_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📅 Выдать документ",
                callback_data=f"admin_set_access_date_{user_id}",
            ),
            InlineKeyboardButton(
                text="❌ Удалить документ",
                callback_data=f"admin_revoke_document_{user_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🏢 Изменить компанию",
                callback_data=f"admin_edit_company_{user_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🗑️ Удалить пользователя",
                callback_data=f"admin_delete_user_{user_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 К результатам поиска", callback_data="admin_search_users"
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_delete_confirm_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления пользователя"""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Да, удалить", callback_data=f"admin_confirm_delete_{user_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Отмена", callback_data=f"admin_user_{user_id}"
            ),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_access_date_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для ввода даты выдачи документа"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📅 Сегодня",
                callback_data=f"admin_set_today_{user_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="❌ Отмена", callback_data=f"admin_user_{user_id}"
            ),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


from typing import Optional


def get_admin_company_keyboard(
    user_id: int, selected_companies: Optional[list[str]] = None
) -> InlineKeyboardMarkup:
    """Клавиатура выбора компаний для администратора"""
    if selected_companies is None:
        selected_companies = []
    buttons = []
    for key, name in settings.COMPANY_FULL_NAMES.items():
        prefix = "✅ " if key in selected_companies else "⬜️ "
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{prefix}{name}",
                    callback_data=f"admin_set_company_toggle_{key}_{user_id}",
                )
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                text="✅ Сохранить",
                callback_data=f"admin_set_company_confirm_{user_id}",
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text="🔙 Отмена",
                callback_data=f"admin_user_{user_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_company_selection_keyboard(
    selected_companies: Optional[list[str]] = None,
) -> InlineKeyboardMarkup:
    """Клавиатура выбора компании при регистрации"""
    if selected_companies is None:
        selected_companies = []
    buttons = []
    for key, name in settings.COMPANY_FULL_NAMES.items():
        prefix = "✅ " if key in selected_companies else "⬜️ "
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{prefix}{name}", callback_data=f"reg_company_toggle_{key}"
                )
            ]
        )

    if selected_companies:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить выбор", callback_data="reg_company_confirm"
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_test_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для отмены теста"""
    buttons = [
        [InlineKeyboardButton(text="❌ Прервать тест", callback_data="test_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_test_notification_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для уведомления администратора о сдаче теста."""
    buttons = [
        [
            InlineKeyboardButton(
                text="📅 Выдать/обновить документ",
                callback_data=f"admin_grant_document_{user_id}",
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_select_group_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="II группа", callback_data=f"admin_select_group_2_{user_id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="III группа", callback_data=f"admin_select_group_3_{user_id}"
        )
    )
    builder.add(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_user_{user_id}")
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def get_admin_revoke_select_group_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="II группа", callback_data=f"admin_revoke_group_2_{user_id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="III группа", callback_data=f"admin_revoke_group_3_{user_id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="Все документы", callback_data=f"admin_revoke_group_all_{user_id}"
        )
    )
    builder.add(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_user_{user_id}")
    )
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def get_paginated_users_keyboard(
    users: list, current_page: int, total_pages: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for user in users:
        text = user.full_name or user.username or f"User {user.telegram_id}"
        builder.add(
            InlineKeyboardButton(text=text, callback_data=f"admin_user_{user.id}")
        )

    builder.adjust(1)

    left_button = (
        InlineKeyboardButton(
            text="⬅️", callback_data=f"admin_list_users_{current_page - 1}"
        )
        if current_page > 1
        else InlineKeyboardButton(text="⏹", callback_data="noop")
    )

    middle_button = InlineKeyboardButton(
        text=f"{current_page}/{total_pages}", callback_data="noop"
    )

    right_button = (
        InlineKeyboardButton(
            text="➡️", callback_data=f"admin_list_users_{current_page + 1}"
        )
        if current_page < total_pages
        else InlineKeyboardButton(text="⏹", callback_data="noop")
    )

    builder.row(left_button, middle_button, right_button)
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin_menu")
    )

    return builder.as_markup()
