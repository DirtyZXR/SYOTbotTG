from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.user import User
from typing import Optional, List, Sequence
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
        companies: Optional[list[str]] = None,
    ) -> User:
        """Создание нового пользователя"""
        user = User(
            telegram_id=telegram_id,
            email=email,
            full_name=full_name,
            full_name_lower=full_name.lower() if full_name else None,
            username=username,
            is_pending=is_pending,
            companies=companies if companies is not None else [],
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

    def get_users_count(self) -> int:
        return self.db.query(User).count()

    def get_users_paginated(self, limit: int, offset: int) -> Sequence[User]:
        return (
            self.db.query(User)
            .order_by(User.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_all_verified_users(self) -> List[User]:
        """Получение всех верифицированных пользователей, кроме админов"""
        return (
            self.db.query(User)
            .filter(User.is_verified == True, User.is_admin == False)
            .all()
        )

    def get_non_admin_users(self) -> List[User]:
        """Получение всех пользователей, кроме админов (для управления руководителями)"""
        return (
            self.db.query(User)
            .filter(User.is_admin == False, User.is_pending == False)
            .order_by(User.full_name_lower)
            .all()
        )

    def get_active_users_for_report(self) -> List[User]:
        """Получение всех активных пользователей (не админов, не ожидающих) для отчёта по срокам"""
        return (
            self.db.query(User)
            .filter(User.is_admin == False, User.is_pending == False)
            .order_by(User.full_name_lower)
            .all()
        )

    def get_supervisor_ids(self) -> List[int]:
        """Получение telegram_id всех руководителей"""
        return [
            row[0]
            for row in self.db.query(User.telegram_id)
            .filter(User.is_supervisor == True)
            .all()
        ]

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

    def set_access_date(
        self, user: User, date: datetime, granted_group: Optional[int] = None
    ) -> User:
        """Устанавливает дату выдачи документа и сбрасывает флаги уведомлений"""
        user.is_verified = True
        user.access_granted_at = date

        if granted_group == 5:
            user.group2_passed_at = date
            user.group3_passed_at = date
            user.group4_passed_at = date
            user.group5_passed_at = date
        elif granted_group == 4:
            user.group2_passed_at = date
            user.group3_passed_at = date
            user.group4_passed_at = date
        elif granted_group == 3:
            user.group2_passed_at = date
            user.group3_passed_at = date
        else:
            user.group2_passed_at = date

        user.notified_7d = False
        user.notified_1d = False
        # Сбрасываем флаги уведомлений по группе 3, 4, 5 т.к. дата изменилась
        user.notified_3g_7d = False
        user.notified_3g_1d = False
        user.notified_3g_exp_7d = False
        user.notified_3g_exp_1d = False
        user.notified_4g_exp_7d = False
        user.notified_4g_exp_1d = False
        user.notified_5g_exp_7d = False
        user.notified_5g_exp_1d = False
        self.db.commit()
        self.db.refresh(user)
        return user

    def unverify_user(self, user: User) -> User:
        """Снятие верификации (допуск истёк)"""
        user.is_verified = False
        self.db.commit()
        self.db.refresh(user)
        return user

    def revoke_document(self, user: User, group_num: Optional[int] = None) -> User:
        """Отзыв документа у пользователя"""
        if group_num == 5:
            user.group5_passed_at = None
        elif group_num == 4:
            user.group5_passed_at = None
            user.group4_passed_at = None
        elif group_num == 3:
            user.group5_passed_at = None
            user.group4_passed_at = None
            user.group3_passed_at = None
        else:
            # Revoke all
            user.group5_passed_at = None
            user.group4_passed_at = None
            user.group3_passed_at = None
            user.group2_passed_at = None
            user.is_verified = False
            user.access_granted_at = None

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

    def set_supervisor(self, user: User, is_supervisor: bool = True) -> User:
        """Назначение/снятие прав руководителя"""
        user.is_supervisor = is_supervisor
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

    def update_user(self, user: User, data: dict) -> User:
        """Обновление произвольных полей пользователя"""
        for key, value in data.items():
            setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    # ==================== Scheduler: Expiry & Notifications ====================

    def get_expired_users(self) -> List[User]:
        """Пользователи с истёкшим допуском (is_verified=True, срок вышел, не админ)"""
        now = datetime.now()
        # При множественных компаниях мы не можем просто использовать User.company != "consulting".
        # Но SQLite JSON не имеет простого оператора != для массивов.
        # Оставим фильтрацию на уровне приложения или сделаем ее проще.
        users = (
            self.db.query(User)
            .filter(
                User.is_verified == True,
                User.is_admin == False,
                User.access_granted_at != None,
                User.access_granted_at <= now - timedelta(days=358),
            )
            .all()
        )
        return [u for u in users if u.companies != ["consulting"]]

    def get_expiring_users(self, days: int, notified_field: str) -> List[User]:
        """Пользователи, чей допуск истекает через N дней (ещё не уведомлены)"""
        now = datetime.now()
        threshold = now + timedelta(days=days)

        users = (
            self.db.query(User)
            .filter(
                User.is_verified == True,
                User.is_admin == False,
                User.access_granted_at != None,
                User.access_granted_at <= threshold - timedelta(days=358),
                User.access_granted_at > now - timedelta(days=358),
                getattr(User, notified_field) == False,
            )
            .all()
        )
        return [u for u in users if u.companies != ["consulting"]]

    def get_users_for_3g_notification(
        self, days: int, notified_field: str
    ) -> List[User]:
        """Пользователи, которым через N дней открывается группа 3"""
        from datetime import datetime, timedelta

        now = datetime.now()
        threshold = now + timedelta(days=days)
        users = (
            self.db.query(User)
            .filter(
                User.is_admin == False,
                User.group2_passed_at != None,
                User.access_granted_at != None,
                User.group3_passed_at == None,  # Ещё не сдал 3
                User.access_granted_at <= threshold - timedelta(days=90),
                User.access_granted_at > now - timedelta(days=90),
                getattr(User, notified_field) == False,
            )
            .all()
        )
        return [u for u in users if u.companies != ["consulting"]]

    def mark_notified(self, user: User, field: str) -> User:
        """Отметить, что уведомление отправлено"""
        setattr(user, field, True)
        self.db.commit()
        self.db.refresh(user)
        return user
