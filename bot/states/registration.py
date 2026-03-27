from aiogram.fsm.state import State, StatesGroup


class RegistrationForm(StatesGroup):
    """Состояния формы регистрации"""

    waiting_for_email = State()  # Ожидание ввода email
    waiting_for_code = State()   # Ожидание ввода кода безопасности
