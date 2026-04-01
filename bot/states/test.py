from aiogram.fsm.state import State, StatesGroup


class TestState(StatesGroup):
    """Состояния прохождения теста"""

    taking_test = State()  # В процессе ответа на вопросы
