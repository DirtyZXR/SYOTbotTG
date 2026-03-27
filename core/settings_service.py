from database import SessionLocal, SettingsRepository
from config import settings
from utils import logger
from typing import Optional


class SettingsService:
    """Сервис работы с настройками системы"""

    def __init__(self):
        pass

    @staticmethod
    def get_security_code() -> Optional[str]:
        """Получение секретного кода"""
        db = SessionLocal()
        settings_repo = SettingsRepository(db)
        code = settings_repo.get_value("security_code")
        db.close()
        return code

    @staticmethod
    def set_security_code(code: str) -> None:
        """Установка секретного кода"""
        db = SessionLocal()
        settings_repo = SettingsRepository(db)
        settings_repo.set_value("security_code", code)
        db.close()

    @staticmethod
    def get_admin_ids() -> list:
        """Получение списка ID всех администраторов"""
        db = SessionLocal()
        user_repo = UserRepository(db)
        users = user_repo.get_all_users()
        admin_ids = [u.telegram_id for u in users if u.is_admin]
        db.close()
        return admin_ids

    @staticmethod
    def initialize_from_env():
        """Инициализация настроек из .env при первом запуске"""
        from database import SessionLocal, SettingsRepository
        from database.user_repo import UserRepository

        db = SessionLocal()
        settings_repo = SettingsRepository(db)
        user_repo = UserRepository(db)

        # Проверяем и инициализируем секретный код
        if not settings_repo.exists("security_code"):
            logger.info("Initializing security code from .env...")
            settings_repo.set_value("security_code", settings.security_code)
            logger.info("Security code saved to database")
        else:
            logger.info("Security code already exists in database")

        # Проверяем первого админа из .env
        super_admin_id = settings.admin_id
        existing_admin = user_repo.get_by_telegram_id(super_admin_id)

        if not existing_admin:
            logger.info(f"Creating first admin from .env (ID: {super_admin_id})...")
            # Создаем первого админа
            user_repo.create_user(
                telegram_id=super_admin_id,
                email=f"admin@intellektika.ru",
                full_name="Super Admin",
                username="superadmin",
            )
            # Делаем админом
            created_user = user_repo.get_by_telegram_id(super_admin_id)
            user_repo.set_admin(created_user, is_admin=True)
            user_repo.verify_user(created_user)
            logger.info(f"First admin created in database (ID: {super_admin_id})")
        else:
            if not existing_admin.is_admin:
                logger.info(f"Assigning admin rights to user from .env (ID: {super_admin_id})...")
                user_repo.set_admin(existing_admin, is_admin=True)
                logger.info(f"Admin rights assigned (ID: {super_admin_id})")
            else:
                logger.info(f"User from .env is already an admin (ID: {super_admin_id})")

        db.close()


# Добавляем импорт UserRepository в конец файла
from database import UserRepository
