from typing import Optional
from database import SessionLocal, UserRepository
from config import settings
from models.user import User
from .settings_service import SettingsService


class AuthService:
    """Сервис аутентификации и авторизации"""

    def __init__(self):
        pass

    @staticmethod
    def get_security_code() -> str:
        """Получение секретного кода (из БД)"""
        code = SettingsService.get_security_code()
        return code if code else settings.security_code

    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """
        Проверка валидности email (формат и домен)
        Возвращает (success, message)
        """
        # Проверяем, что email с корпоративным доменом
        allowed_domains = ["intellectika.ru"]
        if not any(email.endswith(f"@{domain}") for domain in allowed_domains):
            return False, "Email должен быть с корпоративного домена"

        # Проверяем, не занят ли email другим пользователем
        db = SessionLocal()
        user_repo = UserRepository(db)
        existing_user = user_repo.get_by_email(email)
        db.close()

        if existing_user:
            return False, "Этот email уже зарегистрирован в системе"

        return True, "Email корректен"

    @staticmethod
    def register_user(
        telegram_id: int,
        email: str,
        full_name: Optional[str] = None,
        username: Optional[str] = None,
        company: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Регистрация пользователя (создаёт запись с is_pending=True)
        Возвращает (success, message)
        """
        db = SessionLocal()
        user_repo = UserRepository(db)

        # Проверяем, что email с корпоративным доменом
        allowed_domains = ["intellectika.ru"]
        if not any(email.endswith(f"@{domain}") for domain in allowed_domains):
            db.close()
            return False, "Email должен быть с корпоративного домена"

        # Проверяем, не зарегистрирован ли уже пользователь с этим email
        existing_user = user_repo.get_by_email(email)
        if existing_user:
            db.close()
            return False, "Пользователь с таким email уже зарегистрирован"

        # Проверяем, не зарегистрирован ли уже этот telegram_id
        existing_telegram = user_repo.get_by_telegram_id(telegram_id)
        if existing_telegram:
            db.close()
            return False, "Вы уже зарегистрированы в системе"

        # Создаём пользователя со статусом pending
        user = user_repo.create_user(
            telegram_id=telegram_id,
            email=email,
            full_name=full_name,
            username=username,
            is_pending=True,
            company=company,
        )
        db.close()
        return True, "Заявка отправлена"

    @staticmethod
    def is_authorized(telegram_id: int) -> bool:
        """Проверка авторизации пользователя (существует в БД и подтверждён админом)"""
        db = SessionLocal()
        user_repo = UserRepository(db)

        user = user_repo.get_by_telegram_id(telegram_id)
        is_auth = user and not user.is_pending

        db.close()
        return is_auth

    @staticmethod
    def is_pending(telegram_id: int) -> bool:
        """Проверка, ожидает ли пользователь подтверждения"""
        db = SessionLocal()
        user_repo = UserRepository(db)

        user = user_repo.get_by_telegram_id(telegram_id)
        result = user and user.is_pending

        db.close()
        return result

    @staticmethod
    def get_user(telegram_id: int) -> Optional[User]:
        """Получение пользователя"""
        db = SessionLocal()
        user_repo = UserRepository(db)

        user = user_repo.get_by_telegram_id(telegram_id)
        db.close()
        return user

    @staticmethod
    def is_admin(telegram_id: int) -> bool:
        """Проверка админских прав пользователя"""
        db = SessionLocal()
        user_repo = UserRepository(db)

        is_admin = user_repo.is_admin(telegram_id)
        db.close()
        return is_admin
