from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.user import User
from typing import Optional, List
from datetime import datetime, timedelta


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
        is_pending: bool = True,
        company: Optional[str] = None,
    ) -> User:
        """Создание нового пользователя"""
        user = User(
            telegram_id=telegram_id,
            email=email,
            full_name=full_name,
            full_name_lower=full_name.lower() if full_name else None,
            username=username,
            is_pending=is_pending,
            company=company,
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

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_all_users(self) -> List[User]:
        """Получение всех пользователей"""
        return self.db.query(User).all()

    def get_admin_ids(self) -> List[int]:
        """Получение telegram_id всех администраторов"""
        return [
            row[0]
            for row in self.db.query(User.telegram_id)
            .filter(User.is_admin == True)
            .all()
        ]

    # ==================== Approve / Reject ====================

    def approve_user(self, user: User) -> User:
        """Подтверждение регистрации пользователя админом"""
        user.is_pending = False
        self.db.commit()
        self.db.refresh(user)
        return user

    def reject_user(self, user: User) -> None:
        """Отклонение регистрации — удаление пользователя и связанных данных"""
        from models.test_result import TestResult

        self.db.query(TestResult).filter(TestResult.user_id == user.id).delete()
        self.db.delete(user)
        self.db.commit()

    # ==================== Verify / Access Date ====================

    def verify_user(self, user: User) -> User:
        """Верификация пользователя (устаревший метод, оставлен для совместимости)"""
        user.is_verified = True
        user.access_granted_at = datetime.now()
        user.notified_7d = False
        user.notified_1d = False
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_access_date(self, user: User, date: datetime) -> User:
        """Установка даты выдачи документа (начало отсчёта 358 дней)"""
        user.is_verified = True
        user.access_granted_at = date
        user.notified_7d = False
        user.notified_1d = False
        self.db.commit()
        self.db.refresh(user)
        return user

    def unverify_user(self, user: User) -> User:
        """Снятие верификации (допуск истёк)"""
        user.is_verified = False
        self.db.commit()
        self.db.refresh(user)
        return user

    # ==================== Delete ====================

    def delete_user(self, user: User) -> None:
        """Удаление пользователя и связанных данных (результаты тестов)"""
        from models.test_result import TestResult

        self.db.query(TestResult).filter(TestResult.user_id == user.id).delete()
        self.db.delete(user)
        self.db.commit()

    # ==================== Admin ====================

    def set_admin(self, user: User, is_admin: bool = True) -> User:
        """Назначение/снятие прав администратора"""
        user.is_admin = is_admin
        self.db.commit()
        self.db.refresh(user)
        return user

    def is_admin(self, telegram_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        user = self.get_by_telegram_id(telegram_id)
        if user and user.is_admin:
            return True
        return False

    # ==================== Search ====================

    def search_users(self, query: str) -> List[User]:
        """Поиск пользователей по ФИО или email (без учёта регистра)"""
        search_pattern = f"%{query}%"
        return (
            self.db.query(User)
            .filter(
                or_(
                    User.full_name_lower.like(f"%{query.lower()}%"),
                    User.email.ilike(search_pattern),
                )
            )
            .all()
        )

    # ==================== Update ====================

    def update_full_name(self, user: User, full_name: str) -> User:
        """Обновление ФИО пользователя"""
        user.full_name = full_name
        user.full_name_lower = full_name.lower() if full_name else None
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_email(self, user: User, email: str) -> User:
        """Обновление email пользователя"""
        user.email = email
        self.db.commit()
        self.db.refresh(user)
        return user

    # ==================== Scheduler: Expiry & Notifications ====================

    def get_expired_users(self) -> List[User]:
        """Пользователи с истёкшим допуском (is_verified=True, срок вышел, не админ)"""
        now = datetime.now()
        return (
            self.db.query(User)
            .filter(
                User.is_verified == True,
                User.is_admin == False,
                User.company != "consulting",
                User.access_granted_at != None,
                User.access_granted_at + timedelta(days=358) <= now,
            )
            .all()
        )

    def get_expiring_users(self, days: int, notified_field: str) -> List[User]:
        """Пользователи, чей допуск истекает через N дней (ещё не уведомлены)"""
        now = datetime.now()
        threshold = now + timedelta(days=days)

        return (
            self.db.query(User)
            .filter(
                User.is_verified == True,
                User.is_admin == False,
                User.company != "consulting",
                User.access_granted_at != None,
                User.access_granted_at + timedelta(days=358) <= threshold,
                User.access_granted_at + timedelta(days=358) > now,
                getattr(User, notified_field) == False,
            )
            .all()
        )

    def mark_notified(self, user: User, field: str) -> User:
        """Отметить, что уведомление отправлено"""
        setattr(user, field, True)
        self.db.commit()
        self.db.refresh(user)
        return user
