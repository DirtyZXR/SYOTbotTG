from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


class AuthMiddleware(BaseMiddleware):
    """Middleware для проверки авторизации пользователя.

    Пропускает без проверки:
    - Команды /start, /help, /cancel
    - Состояния регистрации (RegistrationForm)
    - Callback cancel_registration

    Для всех остальных действий проверяет:
    - Существует ли пользователь в БД
    - Подтверждён ли он админом (is_pending=False)
    """

    PUBLIC_COMMANDS = {"/start", "/help", "/cancel"}
    PUBLIC_CALLBACKS = {
        "cancel_registration",
        "reg_company_intellectika",
        "reg_company_consulting",
    }
    REGISTRATION_STATE_PREFIX = "RegistrationForm"

    async def __call__(self, handler, event, data):
        user = event.from_user
        if not user:
            return await handler(event, data)

        if self._is_public_action(event, data):
            return await handler(event, data)

        from database import SessionLocal
        from database.user_repo import UserRepository

        db = SessionLocal()
        try:
            user_repo = UserRepository(db)
            db_user = user_repo.get_by_telegram_id(user.id)

            if not db_user:
                if isinstance(event, CallbackQuery):
                    await event.message.edit_text(
                        "❌ <b>Доступ запрещён</b>\n\n"
                        "Вы не зарегистрированы в системе.\n"
                        "Нажмите /start для регистрации.",
                        parse_mode="HTML",
                    )
                    await event.answer()
                else:
                    await event.answer(
                        "❌ Доступ запрещён. Нажмите /start для регистрации."
                    )
                return

            if db_user.is_pending:
                state = data.get("state")
                if state:
                    await state.clear()

                if isinstance(event, CallbackQuery):
                    await event.message.edit_text(
                        "⏳ <b>Регистрация на рассмотрении</b>\n\n"
                        "Ваша заявка ожидает подтверждения администратора.\n"
                        "После одобрения вы получите уведомление.",
                        parse_mode="HTML",
                    )
                    await event.answer()
                else:
                    await event.answer(
                        "⏳ Ваша заявка на рассмотрении. Дождитесь подтверждения администратора."
                    )
                return
        finally:
            db.close()

        return await handler(event, data)

    def _is_public_action(self, event, data) -> bool:
        if isinstance(event, Message):
            if event.text:
                cmd = event.text.split()[0].lower()
                if cmd in self.PUBLIC_COMMANDS:
                    return True

            raw_state = data.get("raw_state")
            if raw_state and self.REGISTRATION_STATE_PREFIX in str(raw_state):
                return True

        elif isinstance(event, CallbackQuery):
            if event.data in self.PUBLIC_CALLBACKS:
                return True

        return False
