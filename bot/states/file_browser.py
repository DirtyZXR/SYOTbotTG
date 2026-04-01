from aiogram.fsm.state import State, StatesGroup


class FileBrowserState(StatesGroup):
    """Состояния браузера файлов"""

    browsing = State()  # Процесс просмотра файлов и папок
    # В состоянии хранятся данные:
    # - current_path: текущий полный путь
    # - relative_path: относительный путь от data/documents
    # - folders: список папок с их хешами
    # - files: список файлов с их хешами


class AdminState(StatesGroup):
    """Состояния админского меню"""

    changing_code = State()  # Ввод нового секретного кода
    searching_users = State()  # Ввод поискового запроса пользователей
    editing_user_full_name = State()  # Редактирование ФИО пользователя
    editing_user_email = State()  # Редактирование email пользователя
    setting_user_access_date = State()  # Ввод даты выдачи документа
    editing_user_company = State()  # Выбор компании пользователя


class ProfileState(StatesGroup):
    """Состояния редактирования профиля пользователя"""

    editing_full_name = State()  # Редактирование своего ФИО
    editing_email = State()  # Редактирование своего email
