from database import SessionLocal, UserRepository
from config import settings
from utils import logger


class SettingsService:
    """Сервис работы с настройками системы"""

    def __init__(self):
        pass

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
        """Инициализация при первом запуске"""
        db = SessionLocal()
        user_repo = UserRepository(db)

        # Проверяем первого админа из .env
        super_admin_id = settings.admin_id
        admin_email = f"admin_{super_admin_id}@intellectika.ru"
        existing_admin = user_repo.get_by_telegram_id(
            super_admin_id
        ) or user_repo.get_by_email(admin_email)

        if not existing_admin:
            logger.info(f"Creating first admin from .env (ID: {super_admin_id})...")
            user_repo.create_user(
                telegram_id=super_admin_id,
                email=admin_email,
                full_name="Super Admin",
                username="superadmin",
                is_pending=False,
            )
            created_user = user_repo.get_by_telegram_id(super_admin_id)
            user_repo.set_admin(created_user, is_admin=True)
            logger.info(f"First admin created in database (ID: {super_admin_id})")
        else:
            if not existing_admin.is_admin:
                logger.info(
                    f"Assigning admin rights to user from .env (ID: {super_admin_id})..."
                )
                user_repo.set_admin(existing_admin, is_admin=True)
                logger.info(f"Admin rights assigned (ID: {super_admin_id})")
            else:
                logger.info(
                    f"User from .env is already an admin (ID: {super_admin_id})"
                )

        db.close()
