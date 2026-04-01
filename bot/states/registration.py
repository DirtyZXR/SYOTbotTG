from aiogram.fsm.state import State, StatesGroup


class RegistrationForm(StatesGroup):
    """Состояния формы регистрации"""

    waiting_for_full_name = State()  # Ожидание ввода ФИО
    waiting_for_email = State()  # Ожидание ввода email
    waiting_for_company = State()  # Выбор компании
