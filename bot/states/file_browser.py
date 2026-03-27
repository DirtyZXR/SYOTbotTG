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
