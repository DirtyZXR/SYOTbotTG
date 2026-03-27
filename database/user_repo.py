from sqlalchemy.orm import Session
from models.user import User
from typing import Optional, List


class UserRepository:
    """Репозиторий для работы с пользователями"""

    def __init__(self, db: Session):
        self.db = db

    def create_user(
        self,
        telegram_id: int,
        email: str,
        full_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> User:
        """Создание нового пользователя"""
        user = User(
            telegram_id=telegram_id,
            email=email,
            full_name=full_name,
            username=username,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя по telegram_id"""
        return self.db.query(User).filter(User.telegram_id == telegram_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        return self.db.query(User).filter(User.email == email).first()

    def verify_user(self, user: User) -> User:
        """Верификация пользователя"""
        from datetime import datetime

        user.is_verified = True
        user.access_granted_at = datetime.now()
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_all_users(self) -> List[User]:
        """Получение всех пользователей"""
        return self.db.query(User).all()

    def delete_user(self, user: User) -> None:
        """Удаление пользователя"""
        self.db.delete(user)
        self.db.commit()

    def set_admin(self, user: User, is_admin: bool = True) -> User:
        """Назначение/снятие прав администратора"""
        user.is_admin = is_admin
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def is_admin(self, telegram_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        user = self.get_by_telegram_id(telegram_id)
        if user:
            return user.is_admin
        # Проверка супер-админа из настроек
        return telegram_id == self._get_super_admin_id()

    def _get_super_admin_id(self) -> int:
        """Получение ID супер-админа из настроек"""
        try:
            from config import settings
            return settings.admin_id
        except:
            return 0
