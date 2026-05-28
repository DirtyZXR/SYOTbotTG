from database import SessionLocal, UserRepository
from models.user import User
from typing import Optional


class AuthService:
    """Сервис аутентификации и авторизации"""

    def __init__(self):
        pass

    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """
        Проверка валидности email (формат и домен)
        Returns (success, message)
        """
        # Check corporate domain
        allowed_domains = ["intellectika.ru"]
        if not any(email.endswith(f"@{domain}") for domain in allowed_domains):
            return False, "Email должен быть с корпоративного домена"

        # Check email uniqueness
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
        companies: Optional[list[str]] = None,
    ) -> tuple[bool, str]:
        """
        Register a user (creates with is_pending=True)
        Returns (success, message)
        """
        db = SessionLocal()
        user_repo = UserRepository(db)

        # Check corporate domain
        allowed_domains = ["intellectika.ru"]
        if not any(email.endswith(f"@{domain}") for domain in allowed_domains):
            db.close()
            return False, "Email должен быть с корпоративным домена"

        # Check email uniqueness
        existing_user = user_repo.get_by_email(email)
        if existing_user:
            db.close()
            return False, "User with this email already registered"

        # Check telegram_id uniqueness
        existing_telegram = user_repo.get_by_telegram_id(telegram_id)
        if existing_telegram:
            db.close()
            return False, "You already registered"

        # Create with pending status
        user = user_repo.create_user(
            telegram_id=telegram_id,
            email=email,
            full_name=full_name,
            username=username,
            is_pending=True,
            companies=companies,
        )
        db.close()
        return True, "Application submitted"

    @staticmethod
    def is_authorized(telegram_id: int) -> bool:
        """Check if user is authorized (exists in DB and confirmed by admin)"""
        db = SessionLocal()
        user_repo = UserRepository(db)

        user = user_repo.get_by_telegram_id(telegram_id)
        is_auth = user and not user.is_pending

        db.close()
        return is_auth

    @staticmethod
    def is_pending(telegram_id: int) -> bool:
        """Check if user is pending confirmation"""
        db = SessionLocal()
        user_repo = UserRepository(db)

        user = user_repo.get_by_telegram_id(telegram_id)
        result = user and user.is_pending

        db.close()
        return result

    @staticmethod
    def get_user(telegram_id: int) -> Optional[User]:
        """Get user"""
        db = SessionLocal()
        user_repo = UserRepository(db)

        user = user_repo.get_by_telegram_id(telegram_id)
        db.close()
        return user

    @staticmethod
    def is_admin(telegram_id: int) -> bool:
        """Check if user is admin"""
        db = SessionLocal()
        user_repo = UserRepository(db)

        is_admin = user_repo.is_admin(telegram_id)
        db.close()
        return is_admin
